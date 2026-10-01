from pathlib import Path
import json
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent.parent
html=root/"frozen/reports/2026-09/dashboard.html"
errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={"width":1440,"height":1000})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(html.as_uri())
    page.wait_for_selector("#totals strong")
    totals=page.locator("#totals strong").all_text_contents()
    initial=page.locator("#issues tr").count()
    assert initial==28,initial
    page.select_option("#kind","all")
    all_rows=page.locator("#issues tr").count()
    assert all_rows==215,all_rows
    page.fill("#search","O-202609-0101")
    matches=page.locator("#issues tr").count()
    assert matches>=1
    assert "O-202609-0101" in page.locator("#issues").inner_text()
    page.fill("#search","")
    page.select_option("#kind","priority")
    page.screenshot(path=str(root/"control/dashboard-review-desktop.png"),full_page=False)
    page.set_viewport_size({"width":390,"height":844})
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.screenshot(path=str(root/"control/dashboard-review-mobile.png"),full_page=False)
    workbook=page.locator("#workbook").get_attribute("href")
    assert (html.parent/workbook).is_file()
    assert not errors,errors
    result={"totals":totals,"priority_rows":initial,"all_action_rows":all_rows,"search_matches":matches,"mobile_horizontal_overflow":False,"javascript_errors":errors,"workbook_link":workbook,"rendered_from":"frozen/reports/2026-09/dashboard.html"}
    (root/"control/dashboard-review.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    browser.close()
