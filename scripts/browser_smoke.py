"""Optional real-browser counter smoke check; creates only temporary records.
Run: .venv/bin/python scripts/browser_smoke.py
Requires: pip install -r requirements-dev.txt; python -m playwright install chromium
"""
import sys
import tempfile
from pathlib import Path
from threading import Thread
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
with tempfile.TemporaryDirectory(prefix="apos-browser-") as directory:
    app=create_app({"DATABASE": str(Path(directory)/"preview.sqlite3"), "SECRET_KEY": "isolated-preview-key", "STAFF_PASSWORD": "preview-admin-password", "TESTING": True})
    client=app.test_client();client.get('/login')
    with client.session_transaction() as s: token=s['csrf']
    client.post('/login',data={'csrf':token,'password':'preview-admin-password'})
    client.get('/')
    with client.session_transaction() as s:s['lang']='en';token=s['csrf']
    def post(path,**data):return client.post(path,data={'csrf':token,**data})
    post('/members',name='Alex Robin Taylor',code='M001')
    for name,price in [('Lager','3.50'),('Apple juice','2.50'),('Cola','2.80'),('Sparkling water','2.00'),('Coffee','2.20'),('Alcohol-free wheat beer with a very long product name','3.80')]:post('/products',name=name,price=price,usd_price=price)
    post('/tabs',member_id='1');post('/tabs/1/items',product_id='1',quantity='2');post('/tabs/1/items',product_id='2',quantity='1')
    server=make_server("127.0.0.1",0,app,threaded=True)
    base=f"http://127.0.0.1:{server.server_port}"
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1024,'height':900})
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(f'{base}/login');page.locator('input[name=password]').fill('preview-admin-password');page.locator('form:has(input[name=password]) button').click();page.locator('.personal-menu summary').click();page.locator('select[name=lang]').select_option('en');page.locator('form[action="/language"] button').click()
            page.goto(f'{base}/tabs/1')
            assert page.locator('.product-tile').count()==6
            page.screenshot(path='/tmp/apos-dark-tablet.png',full_page=True)
            for width in [1440,1024,768,390]:
                page.set_viewport_size({'width':width,'height':900})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),f'Overflow at {width}'
                print('No horizontal overflow:',width)
            page.screenshot(path='/tmp/apos-dark-mobile.png',full_page=True)
            page.set_viewport_size({'width':1024,'height':900})
            page.locator('[data-filter=".product-tile"]').fill('no match')
            assert page.locator('[data-filter-empty]').is_visible()
            page.locator('[data-filter=".product-tile"]').fill('Coffee')
            page.locator('[data-step="1"]').click();assert page.locator('#order-quantity').input_value()=='2'
            page.locator('.product-tile:visible').click();page.wait_for_url('**/tabs/1')
            assert '2 × Coffee' in page.locator('.order-lines').inner_text()
            page.locator('[data-partial]').click();page.locator('#payment-amount').fill('2.00');page.locator('.payment-submit').click();page.wait_for_url('**/receipts/*');assert page.locator('.receipt-patron-access a').first.is_visible()
            page.goto(f'{base}/tabs/1');assert '€2.00' in page.locator('.order-summary').inner_text()
            page.locator('[data-fill]').click();page.locator('input[value=card]').check();page.locator('.payment-submit').click();page.wait_for_url('**/receipts/*');assert page.locator('.receipt-patron-access a').first.is_visible()
            page.goto(f'{base}/admin')
            for width in [1024,390]:
                page.set_viewport_size({'width':width,'height':900})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),f'Admin overflow {width}'
            page.locator('input[name=tagline]').fill('Association ' + 'Long' * 20)
            page.locator('.settings-form > button').click()
            assert 'APOS — Association' in page.title()
            for width in [1024,390]:
                page.set_viewport_size({'width':width,'height':900})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),f'Tagline overflow {width}'
            page.goto(f'{base}/')
            page.locator('form[action="/guests"] button').click()
            page.locator('.guest-access summary').click()
            patron_url = page.locator('.guest-access a').last.get_attribute('href')
            page.goto(patron_url)
            page.locator('form[action$="/name"] input[name=name]').fill('Alex Guest')
            page.locator('form[action$="/name"] button').click()
            assert page.locator('form[action$="/name"] input[name=name]').input_value()=='Alex Guest'
            import io
            from PIL import Image
            photo=io.BytesIO();Image.new('RGB',(80,80),(40,100,80)).save(photo,format='PNG')
            page.locator('input[name=photo]').set_input_files({'name':'test.png','mimeType':'image/png','buffer':photo.getvalue()})
            page.locator('form[action$="/photo"] button').click()
            assert page.locator('.bon-photo').evaluate('img => img.complete && img.naturalWidth === 256')
            page.screenshot(path='/tmp/apos-guest-photo-mobile.png',full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),'Guest page overflow'
            page.screenshot(path='/tmp/apos-guest-photo-mobile.png',full_page=True)
            assert not errors,errors
            print('PASS: product search, quantity, actual order submission, partial cash and full card settlement, admin responsive, long tagline, guest rename/photo rendering, no JavaScript errors')
            browser.close()
    finally:
        server.shutdown();thread.join()
