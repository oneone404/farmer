package core

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

type GlobalConfig struct {
	ADBPath                string  `json:"adb_path"`
	LDPlayerPath           string  `json:"ldplayer_path"`
	UseTimeGate            bool    `json:"use_time_gate"`
	FirstRunImmediate      bool    `json:"first_run_immediate"`
	Threshold              float64 `json:"threshold"`
	ScanInterval           int     `json:"scan_interval"`
	EnableBuyFruits        bool    `json:"enable_buy_fruits"`
	EnableBuyVoi           bool    `json:"enable_buy_voi"`
	EnableHarvestSell      bool    `json:"enable_harvest_sell"`
	HarvestSellCycles      int     `json:"harvest_sell_cycles"`
	SellCyclesAfterHarvest int     `json:"sell_cycles_after_harvest"`
	ScrollStart            []int   `json:"scroll_start"`
	ScrollEnd              []int   `json:"scroll_end"`
}

type Config struct {
	AppDir       string
	AppDataDir   string
	ConfigDir    string
	GlobalConfig GlobalConfig
	ROI          ROIConfig
	Buttons      ButtonConfig
}

type ROIConfig struct {
	BtnCuaHang      []int `json:"btn_cua_hang"`
	BtnOpenCuaHang  []int `json:"btn_open_cua_hang"`
	BtnOpenCuaHang2 []int `json:"btn_open_cua_hang_2"`
	PanelCheck      []int `json:"panel_check"`
	PanelAll        []int `json:"panel_all"`
	List            []int `json:"list"`
	Buy             []int `json:"buy"`
	ThuHoachAll     []int `json:"thu_hoach_all"`
	ConfirmTh       []int `json:"confirm_th"`
}

type ButtonConfig struct {
	Buy              []int `json:"buy"`
	MaxQty           []int `json:"max_qty"`
	Plus             []int `json:"plus"`
	Confirm          []int `json:"confirm"`
	CloseFruit1      []int `json:"close_fruit_1"`
	CloseFruit2      []int `json:"close_fruit_2"`
	PanelVoiSelect   []int `json:"panel_voi_select"`
	OpenThSub        []int `json:"open_th_sub"`
	HarvestAll       []int `json:"harvest_all"`
	CloseTh          []int `json:"close_th"`
	OpenBanSub       []int `json:"open_ban_sub"`
	SelectAllProduce []int `json:"select_all_produce"`
	Sell             []int `json:"sell"`
	OkSell           []int `json:"ok_sell"`
	CloseBan         []int `json:"close_ban"`
}

func NewConfig() *Config {
	appData := os.Getenv("APPDATA")
	if appData == "" {
		appData = os.Getenv("HOME")
	}
	farmerDir := filepath.Join(appData, "Farmer")
	configDir := filepath.Join(farmerDir, "configs")

	roi := ROIConfig{
		BtnCuaHang:      []int{1280, 80, 1800, 370},
		BtnOpenCuaHang:  []int{785, 10, 1150, 615},
		BtnOpenCuaHang2: []int{1255, 400, 1650, 540},
		PanelCheck:      []int{180, 50, 520, 165},
		PanelAll:        []int{200, 160, 380, 1024},
		List:            []int{610, 150, 1710, 660},
		Buy:             []int{1010, 790, 1380, 1005},
		ThuHoachAll:     []int{1515, 940, 1900, 1060},
		ConfirmTh:       []int{950, 700, 1405, 910},
	}

	buttons := ButtonConfig{
		Buy:              []int{1240, 910},
		MaxQty:           []int{1228, 683},
		Plus:             []int{1400, 690},
		Confirm:          []int{985, 785},
		CloseFruit1:      []int{1690, 115},
		CloseFruit2:      []int{1310, 700},
		PanelVoiSelect:   []int{1320, 590},
		OpenThSub:        []int{770, 395},
		HarvestAll:       []int{1700, 1000},
		CloseTh:          []int{1840, 70},
		OpenBanSub:       []int{1325, 590},
		SelectAllProduce: []int{1245, 955},
		Sell:             []int{1565, 960},
		OkSell:           []int{965, 830},
		CloseBan:         []int{1840, 70},
	}

	exePath, _ := os.Executable()
	appDir := filepath.Dir(exePath)

	// When using "go run", executable is in temp folder
	// Use working directory instead
	if strings.Contains(appDir, "go-build") || strings.Contains(appDir, "Temp") {
		appDir, _ = os.Getwd()
	}

	c := &Config{
		AppDir:     appDir,
		AppDataDir: farmerDir,
		ConfigDir:  configDir,
		ROI:        roi,
		Buttons:    buttons,
	}

	c.LoadGlobal()
	return c
}

func (c *Config) LoadGlobal() {
	configFile := filepath.Join(c.ConfigDir, "global.json")
	if _, err := os.Stat(configFile); err == nil {
		data, _ := os.ReadFile(configFile)
		json.Unmarshal(data, &c.GlobalConfig)
	} else {
		c.GlobalConfig = GlobalConfig{
			ADBPath:           filepath.Join(c.AppDir, "..", "backend", "assets", "adb", "adb.exe"),
			LDPlayerPath:      `C:\LDPlayer\LDPlayer9`,
			Threshold:         0.95,
			ScanInterval:      3,
			EnableBuyFruits:   true,
			EnableBuyVoi:      true,
			EnableHarvestSell: true,
			HarvestSellCycles: 1,
			ScrollStart:       []int{600, 900},
			ScrollEnd:         []int{600, 450},
		}
		// If adb not found at default location, try just "adb.exe"
		if _, err := os.Stat(c.GlobalConfig.ADBPath); err != nil {
			c.GlobalConfig.ADBPath = "adb.exe"
		}
	}
}

func (c *Config) GetAssetPath(sub ...string) string {
	// Try multiple locations for assets
	// When running from backend-go folder via "go run main.go"
	// Assets are in ../backend/assets
	paths := []string{
		// Running from backend-go folder (development)
		filepath.Join(append([]string{c.AppDir, "..", "backend", "assets"}, sub...)...),
		// Same level assets folder
		filepath.Join(append([]string{c.AppDir, "assets"}, sub...)...),
		// Bundled app
		filepath.Join(append([]string{c.AppDir, "_up_", "backend", "assets"}, sub...)...),
	}

	for _, p := range paths {
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}
	// Debug: print searched paths
	fmt.Printf("[CONFIG] Asset not found. Searched: %v\n", paths)
	return filepath.Join(append([]string{c.AppDir, "assets"}, sub...)...)
}

func (c *Config) GetTemplatePath(name string) string {
	return c.GetAssetPath("templates", name+".png")
}

func (c *Config) GetFruitPath(name string) string {
	mapping := map[string]string{
		"Dâu Tây": "fruit_dau_tay",
		"Cà Rốt":  "fruit_ca_rot",
	}
	fname := mapping[name]
	if fname == "" {
		return ""
	}
	return c.GetAssetPath("fruits", fname+".png")
}

func (c *Config) GetButtonPath(name string) string {
	mapping := map[string]string{
		"cua_hang":        "btn_cua_hang",
		"open_cua_hang":   "btn_open_cua_hang",
		"open_cua_hang_2": "btn_open_cua_hang2",
	}
	fname := mapping[name]
	if fname == "" {
		return ""
	}
	return c.GetAssetPath("buttons", fname+".png")
}

func (c *Config) GetAllFruits() map[string]string {
	fruits := map[string]string{
		"Dâu Tây":   "fruit_dau_tay",
		"Cà Rốt":    "fruit_ca_rot",
		"Mảng Cầu":  "fruit_mang_cau",
		"Bí Ngô":    "fruit_bi_ngo",
		"Dưa Hấu":   "fruit_dua_hau",
		"Đu Đủ":     "fruit_du_du",
		"Khế":       "fruit_khe",
		"Táo Đường": "fruit_tao_duong",
		"Xoài":      "fruit_xoai",
		"Nho":       "fruit_nho",
		"Đậu":       "fruit_dau",
		"Dừa":       "fruit_dua",
	}
	result := make(map[string]string)
	for name, fname := range fruits {
		result[name] = c.GetAssetPath("fruits", fname+".png")
	}
	return result
}

func (c *Config) GetFruits() map[string]interface{} {
	fruits := c.GetAllFruits()
	result := make(map[string]interface{})
	for name, path := range fruits {
		result[name] = map[string]interface{}{"img": path, "buy": true}
	}
	return result
}
