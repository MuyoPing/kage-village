-- Extract the KageVillage folder into the executor's workspace directory.
local env=(getgenv and getgenv()) or _G
env.KageVillageSource={LocalFolder="KageVillage",BaseUrl="",Language="ko",Quality="High",Volume=0.55}
assert(readfile and loadstring,"This launcher requires local file access and loadstring")
return assert(loadstring(readfile("KageVillage/KageVillage.luau"),"@KageVillage"))()
