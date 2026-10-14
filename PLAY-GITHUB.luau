-- Replace this root with the uploaded repository and preferably a commit SHA.
-- Example format only: https://raw.githubusercontent.com/OWNER/REPO/COMMIT
local BASE_URL="https://raw.githubusercontent.com/MuyoPing/kage-village/37069aa3cab4a2b8b8adc1434be7305d2f8d09ee"
assert(BASE_URL:match("^https://raw%.githubusercontent%.com/"),"Set BASE_URL to the uploaded GitHub repository raw root")
local env=(getgenv and getgenv()) or _G
env.KageVillageSource={BaseUrl=BASE_URL,Language="ko",Quality="High",Volume=0.55}
return assert(loadstring(game:HttpGet(BASE_URL.."/KageVillage.luau"),"@KageVillage"))()
