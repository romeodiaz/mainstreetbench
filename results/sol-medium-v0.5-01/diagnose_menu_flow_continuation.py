"""Authorized continuation after correcting only a diagnostic-helper locator; no grading or submission changes."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
import tempfile
import time

ROOT = Path('/Users/romeodiaz/Documents/BenchRuns/mainstreetbench/v0.5-sol-medium-20261001T070225Z')
GRADE = ROOT / 'grading'
CONTROL = ROOT / 'control'
SITE_ROOT = ROOT / 'frozen'
sys.path.insert(0, str(GRADE / 'trusted/tasks/ordering-site/hidden_tests'))
from sitectl import Site, NOW
from playwright.sync_api import sync_playwright


def hashes(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise AssertionError('Unexpected symlink: ' + str(path))
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def main():
    before = hashes(SITE_ROOT)
    sources = json.loads((GRADE / 'source-manifest.json').read_text())
    evidence_names = ['report.json', 'run.json', 'server-launches.jsonl', 'browser-launches.jsonl']
    original_evidence = {name: hashlib.sha256((GRADE / name).read_bytes()).hexdigest() for name in evidence_names}
    result = {
        'purpose': 'Authorized short continuation: correct only the helper pickup-time label locator and observe one normal date-first order in a fresh database/context; not a counterfactual grade.',
        'site': str(SITE_ROOT),
        'requested_date': '2026-10-10',
        'requested_time': '10:00',
        'database': 'new throwaway database in existing sandbox scratch',
        'server_sandbox': str(GRADE / 'site.sb'),
        'source_commit': 'bee5fa06f3c15cba120e75271470f89911ba818f',
        'page_errors': [],
        'request_failures': [],
        'api_responses': [],
        'screenshots': [],
        'grade_rerun': False,
        'submission_modified': False,
    }
    scratch = Path(tempfile.mkdtemp(prefix='menu-flow-diagnostic-', dir=GRADE / 'scratch/tmp'))
    site = None
    context = None
    browser = None
    started = time.monotonic()
    try:
        site = Site(SITE_ROOT, scratch / 'bakery.db')
        with sync_playwright() as playwright:
            import os
            browser = playwright.chromium.launch(executable_path=os.environ['CHROMIUM_PATH'], args=['--disable-background-networking', '--disable-component-update', '--no-first-run'])
            context = browser.new_context(base_url=site.base, timezone_id='UTC')
            context.set_default_timeout(5000)
            context.clock.set_fixed_time(dt.datetime.fromisoformat(NOW).replace(tzinfo=dt.timezone.utc))
            page = context.new_page()
            page.on('pageerror', lambda error: result['page_errors'].append(str(error)))
            page.on('requestfailed', lambda request: result['request_failures'].append({'url': request.url, 'failure': request.failure}))
            page.on('response', lambda response: result['api_responses'].append({'method': response.request.method, 'url': response.url, 'status': response.status}) if '/api/' in response.url else None)
            page.goto('/')
            page.wait_for_load_state('networkidle')
            date = page.get_by_label('Pickup date', exact=True)
            bread = page.locator('li[data-sku="BREAD9"]').get_by_role('button', name='Add', exact=True)
            result['initial_menu'] = {
                'date_value': date.input_value(),
                'bread_add_disabled': bread.is_disabled(),
                'all_add_buttons_disabled': page.locator('button.add').evaluate_all('buttons => buttons.every(b => b.disabled)'),
                'instructions': page.locator('.lede').inner_text(),
                'cart_count': page.locator('#cart-count').inner_text(),
            }
            screenshot = CONTROL / 'diagnostic-continuation-menu-before.png'
            page.screenshot(path=str(screenshot), full_page=True)
            result['screenshots'].append(str(screenshot))
            date.fill('2026-10-10')
            date.dispatch_event('change')
            date.blur()
            page.wait_for_function('!document.querySelector("button.add[data-sku=BREAD9]").disabled')
            page.wait_for_load_state('networkidle')
            result['after_menu_date'] = {
                'date_value': date.input_value(),
                'bread_add_enabled': bread.is_enabled(),
                'menu_error': page.locator('#menu-error').inner_text(),
            }
            bread.click()
            bread.click()
            result['after_adding_bread'] = {'cart_count': page.locator('#cart-count').inner_text(), 'cart': page.evaluate('readCart()')}
            screenshot = CONTROL / 'diagnostic-continuation-menu-after.png'
            page.screenshot(path=str(screenshot), full_page=True)
            result['screenshots'].append(str(screenshot))
            page.get_by_role('link', name=re.compile(r'^Cart')).click()
            page.wait_for_load_state('networkidle')
            checkout_date = page.get_by_label('Pickup date', exact=True)
            pickup_time = page.get_by_label(re.compile(r'Pickup time', re.I))
            result['checkout_initial'] = {
                'url': page.url,
                'inherited_menu_date': checkout_date.input_value(),
                'pickup_options': pickup_time.locator('option').evaluate_all('options => options.map(o => ({value:o.value,label:o.textContent,disabled:o.disabled}))'),
            }
            page.get_by_label('Name', exact=True).fill('Diagnostic Customer')
            page.get_by_label('Email', exact=True).fill('diagnostic@example.com')
            page.get_by_label('Phone', exact=True).fill('555-0100')
            if checkout_date.input_value() != '2026-10-10':
                checkout_date.fill('2026-10-10')
                checkout_date.dispatch_event('change')
            pickup_time.select_option('10:00')
            pickup_time.dispatch_event('change')
            page.wait_for_function('!document.querySelector("button[type=submit]").disabled')
            page.wait_for_load_state('networkidle')
            result['checkout_before_submit'] = {
                'date': checkout_date.input_value(),
                'time': pickup_time.input_value(),
                'quote': page.locator('#quote').inner_text(),
                'error': page.locator('#checkout-error').inner_text(),
                'submit_enabled': page.get_by_role('button', name='Place order', exact=True).is_enabled(),
            }
            page.get_by_role('button', name='Place order', exact=True).click()
            page.wait_for_url(re.compile(r'/order/\d+'))
            page.wait_for_load_state('networkidle')
            result['confirmation'] = {'url':page.url,'body':page.inner_text('body')}
            result['order_placed'] = True
            screenshot = CONTROL / 'diagnostic-continuation-order-confirmation.png'
            page.screenshot(path=str(screenshot), full_page=True)
            result['screenshots'].append(str(screenshot))
            result['browser_version'] = browser.version
            context.close()
            context = None
            browser.close()
            browser = None
    except Exception as error:
        result['diagnostic_error'] = {'type':type(error).__name__,'message':str(error)}
    finally:
        if context is not None:
            try:
                context.close()
            except Exception:
                pass
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        if site is not None:
            site.stop()
        shutil.rmtree(scratch, ignore_errors=True)
        result['elapsed_seconds'] = round(time.monotonic() - started, 3)
        result['frozen_hashes_unchanged'] = before == hashes(SITE_ROOT)
        result['trusted_hashes_unchanged'] = all(hashlib.sha256((GRADE / 'trusted' / name).read_bytes()).hexdigest() == digest for name, digest in sources.items())
        result['original_grading_evidence_unchanged'] = all(hashlib.sha256((GRADE / name).read_bytes()).hexdigest() == digest for name, digest in original_evidence.items())
        (CONTROL / 'menu-flow-continuation.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
        assert result['frozen_hashes_unchanged'] and result['trusted_hashes_unchanged'] and result['original_grading_evidence_unchanged'], 'Evidence changed'


if __name__ == '__main__':
    main()
