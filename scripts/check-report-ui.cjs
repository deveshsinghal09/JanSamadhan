const {chromium}=require('C:/Users/DELL/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 const login=await context.request.post('http://127.0.0.1:3001/api/auth/login',{data:{email:'citizen@demo.in',password:'Review@123'}});if(!login.ok())throw Error('Demo sign-in failed');
 const page=await context.newPage();await page.goto('http://127.0.0.1:3001/');await page.getByRole('button',{name:'Report an issue',exact:true}).first().click();
 await page.getByPlaceholder('For example: Garbage has not been collected near the market in Hazratganj for three days.').fill('There is a deep pothole in the municipal road near Hazratganj market. Repair the broken road surface.');
 await page.getByRole('button',{name:'Review text + photo',exact:true}).click();
 await page.getByText('Proposed complaint category',{exact:true}).waitFor();
 await page.screenshot({path:'.training-tmp/report-desktop.png',fullPage:true});
 console.log('Desktop overflow',await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth));
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:'.training-tmp/report-mobile.png',fullPage:true});
 console.log('Mobile overflow',await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth));
 await browser.close();
})().catch(e=>{console.error(e.message);process.exitCode=1});
