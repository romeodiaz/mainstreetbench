"""Read-only post-grade diagnostic of the frozen checkout; no repairs or regrade."""
import datetime as dt
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

RUN = Path(__file__).resolve().parent.parent
SITE_ROOT = RUN/'frozen'
HIDDEN = RUN/'grading/trusted/tasks/ordering-site/hidden_tests'
sys.path.insert(0, str(HIDDEN))
from sitectl import Site, NOW, SATURDAY
from playwright.sync_api import sync_playwright


def hashes():
    return {p.relative_to(SITE_ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in SITE_ROOT.rglob('*') if p.is_file()}

before = hashes()
db_dir = Path(tempfile.mkdtemp(prefix='checkout-diagnostic-', dir=RUN/'grading/scratch/tmp'))
site = None
result = {'purpose':'Read-only post-grade checkout diagnostic; no repair, score changes, or full regrade.',
          'frozen_site':str(SITE_ROOT), 'test_database':'fresh disposable database', 'fixed_clock':NOW,
          'page_errors':[], 'console_errors':[], 'requests':[]}
try:
    site = Site(SITE_ROOT, db_dir/'bakery.db')
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=sys.argv[1], chromium_sandbox=True,
                                     args=['--disable-background-networking','--disable-component-update','--no-first-run'])
        context = browser.new_context(timezone_id='UTC', base_url=site.base)
        context.clock.set_fixed_time(dt.datetime.fromisoformat(NOW).replace(tzinfo=dt.timezone.utc))
        page = context.new_page()
        page.on('pageerror', lambda error:result['page_errors'].append(str(error)))
        page.on('console', lambda msg:result['console_errors'].append(msg.text) if msg.type=='error' else None)
        page.on('request', lambda req:result['requests'].append({'method':req.method,'url':req.url}))
        page.goto('/')
        page.locator('[data-sku="BREAD9"]').get_by_role('button',name='Add').first.click()
        page.goto('/checkout')
        page.wait_for_load_state('networkidle')
        result['script_load_order']=page.locator('script[src]').evaluate_all('els => els.map(e => e.getAttribute("src"))')
        result['time_options_before_date']=page.locator('select[name="pickup_time"] option').evaluate_all(
            'els => els.map(e => ({value:e.value,text:e.textContent,disabled:e.disabled}))')
        date = page.locator('[name="pickup_date"]')
        date.fill(SATURDAY)
        date.dispatch_event('change')
        date.blur()
        page.wait_for_timeout(600)
        result['chosen_pickup_date']=date.input_value()
        result['time_options_after_date']=page.locator('select[name="pickup_time"] option').evaluate_all(
            'els => els.map(e => ({value:e.value,text:e.textContent,disabled:e.disabled}))')
        result['readCart_type_after_full_load']=page.evaluate('typeof readCart')
        result['time_required']=page.locator('select[name="pickup_time"]').evaluate('e => e.required')
        result['availability_text']=page.locator('#availability').inner_text()
        result['pickup_time_requests']=[req for req in result['requests'] if '/api/pickup-times' in req['url']]
        page.screenshot(path=str(RUN/'control/diagnostic-checkout.png'),full_page=True)
        result['browser_version']=browser.version
        context.close()
        browser.close()
finally:
    if site is not None:site.stop()
    shutil.rmtree(db_dir,ignore_errors=True)
result['frozen_file_hashes_unchanged']=before==hashes()
result['confirmed']=(any('readCart is not defined' in error for error in result['page_errors']) and
                     result['time_options_after_date']==result['time_options_before_date'] and
                     not result['pickup_time_requests'] and result['frozen_file_hashes_unchanged'])
(RUN/'control/checkout-diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
assert result['confirmed']
