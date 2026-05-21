package modules

import (
	"farmer-backend-go/core"
	"fmt"
	"image"
	"sort"
	"time"
)

type BuyFruitsModule struct {
	ADB    *core.ADBController
	Img    *core.ImageProcessor
	Config *core.Config

	// Templates
	panelTpl    image.Image
	soldTpl     image.Image
	soldListTpl image.Image
	btnCuaHang  image.Image
	btnOpen1    image.Image
	btnOpen2    image.Image
	fruitTpls   map[string]image.Image

	// State
	checked map[string]bool
	bought  map[string]bool
	soldOut []string
}

func NewBuyFruitsModule(adb *core.ADBController, img *core.ImageProcessor, cfg *core.Config) *BuyFruitsModule {
	m := &BuyFruitsModule{
		ADB:       adb,
		Img:       img,
		Config:    cfg,
		fruitTpls: make(map[string]image.Image),
	}
	m.loadTemplates()
	return m
}

func (m *BuyFruitsModule) loadTemplates() {
	fmt.Println("[FRUIT] Loading templates seriously...")

	m.panelTpl, _ = m.Img.LoadTemplate(m.Config.GetTemplatePath("panel_buy"))
	m.soldTpl, _ = m.Img.LoadTemplate(m.Config.GetTemplatePath("sold_out"))
	m.soldListTpl, _ = m.Img.LoadTemplate(m.Config.GetTemplatePath("sold_out_list"))
	m.btnCuaHang, _ = m.Img.LoadTemplate(m.Config.GetButtonPath("cua_hang"))
	m.btnOpen1, _ = m.Img.LoadTemplate(m.Config.GetButtonPath("open_cua_hang"))
	m.btnOpen2, _ = m.Img.LoadTemplate(m.Config.GetButtonPath("open_cua_hang_2"))

	// Load fruit templates
	fruits := m.Config.GetAllFruits()
	for name, path := range fruits {
		tpl, err := m.Img.LoadTemplate(path)
		if err == nil && tpl != nil {
			m.fruitTpls[name] = tpl
		}
	}
	fmt.Printf("[FRUIT] Total %d fruit templates loaded\n", len(m.fruitTpls))
}

func (m *BuyFruitsModule) scrollToTop() {
	fmt.Println("[FRUIT] Reseting position: Scrolling to top...")
	for i := 0; i < 3; i++ {
		m.ADB.Swipe(600, 400, 600, 1000, 200)
		time.Sleep(500 * time.Millisecond)
	}
}

func (m *BuyFruitsModule) waitForTemplate(tpl image.Image, roi []int, timeout time.Duration) *image.Point {
	if tpl == nil {
		return nil
	}
	start := time.Now()
	for time.Since(start) < timeout {
		png, err := m.ADB.Screencap()
		if err != nil {
			time.Sleep(500 * time.Millisecond)
			continue
		}
		screen, err := m.Img.DecodeScreenshot(png)
		if err != nil || screen == nil {
			time.Sleep(500 * time.Millisecond)
			continue
		}

		cropped := m.Img.Crop(screen, roi)
		res := m.Img.Match(cropped, tpl)
		if res.Confidence >= m.Config.GlobalConfig.Threshold {
			cx := roi[0] + res.Point.X + res.Size.X/2
			cy := roi[1] + res.Point.Y + res.Size.Y/2
			return &image.Point{X: cx, Y: cy}
		}
		time.Sleep(500 * time.Millisecond)
	}
	return nil
}

func (m *BuyFruitsModule) EnsurePanelOpen() bool {
	png, err := m.ADB.Screencap()
	if err != nil {
		return false
	}
	screen, err := m.Img.DecodeScreenshot(png)
	if err != nil || screen == nil {
		return false
	}

	// 1. Check if panel is already open
	if m.panelTpl != nil {
		roi := m.Img.Crop(screen, m.Config.ROI.PanelCheck)
		res := m.Img.Match(roi, m.panelTpl)
		if res.Confidence >= m.Config.GlobalConfig.Threshold {
			fmt.Println("[FRUIT] Shop panel is already open")
			return true
		}
	}

	fmt.Println("[FRUIT] Shop panel closed - Following opening sequence...")

	// 2. Click Shop button
	pos := m.waitForTemplate(m.btnCuaHang, m.Config.ROI.BtnCuaHang, 8*time.Second)
	if pos != nil {
		m.ADB.Tap(pos.X, pos.Y)
		time.Sleep(1 * time.Second)
	} else {
		fmt.Println("[FRUIT] Button Shop not found")
		return false
	}

	// 3. Click Open 1
	pos1 := m.waitForTemplate(m.btnOpen1, m.Config.ROI.BtnOpenCuaHang, 8*time.Second)
	if pos1 != nil {
		m.ADB.Tap(pos1.X, pos1.Y)
		time.Sleep(1 * time.Second)
	} else {
		fmt.Println("[FRUIT] Open button 1 not found")
		return false
	}

	// 4. Click Open 2
	pos2 := m.waitForTemplate(m.btnOpen2, m.Config.ROI.BtnOpenCuaHang2, 8*time.Second)
	if pos2 != nil {
		m.ADB.Tap(pos2.X, pos2.Y)
		time.Sleep(2 * time.Second)
		return true
	} else {
		fmt.Println("[FRUIT] Open button 2 not found")
		return false
	}
}

func (m *BuyFruitsModule) Run() error {
	fmt.Println("STATUS: [MODULE] Buy Fruits")

	if !m.EnsurePanelOpen() {
		return fmt.Errorf("failed to open panel")
	}

	m.checked = make(map[string]bool)
	m.bought = make(map[string]bool)
	m.soldOut = []string{}

	// Trigger initial scroll state
	fmt.Println("[FRUIT] Initializing shop scroll area...")
	m.ADB.Tap(290, 630)
	time.Sleep(1 * time.Second)

	// In Go, map order is random. We sort them to have a deterministic order like Python's dict.
	fruitNames := make([]string, 0, len(m.fruitTpls))
	for name := range m.fruitTpls {
		fruitNames = append(fruitNames, name)
	}
	sort.Strings(fruitNames)
	activeFruitsCount := len(fruitNames)

	// Set threshold from config
	threshold := m.Config.GlobalConfig.Threshold
	if threshold == 0 {
		threshold = 0.95
	}

ScanLoop:
	for attempt := 1; attempt <= 2; attempt++ {
		fmt.Printf("[FRUIT] Starting Scan Attempt %d/2\n", attempt)
		if attempt > 1 {
			m.scrollToTop()
		}

		scrollCount := 0
		maxScrolls := 10 // Increase limit for robustness

		for len(m.checked) < activeFruitsCount && scrollCount < maxScrolls {
			png, err := m.ADB.Screencap()
			if err != nil {
				time.Sleep(1 * time.Second)
				continue
			}
			screen, err := m.Img.DecodeScreenshot(png)
			if err != nil || screen == nil {
				continue
			}

			panel := m.Img.Crop(screen, m.Config.ROI.PanelAll)

			// 1. Identify targets in view
			type fruitTarget struct {
				name string
				pos  image.Point
				size image.Point
			}
			targetsInView := []fruitTarget{}

			for _, name := range fruitNames {
				if m.checked[name] {
					continue
				}

				tpl := m.fruitTpls[name]
				res := m.Img.Match(panel, tpl)

				if res.Confidence >= threshold {
					cx := m.Config.ROI.PanelAll[0] + res.Point.X + res.Size.X/2
					cy := m.Config.ROI.PanelAll[1] + res.Point.Y + res.Size.Y/2

					// Optional: Python's list sold out check
					if m.soldListTpl != nil {
						// checkRoi = (cx + size[0]//2, cy - size[1]//2, cx + 450, cy + size[1]//2 + 50)
						cRoi := []int{
							cx + res.Size.X/2,
							cy - res.Size.Y/2,
							cx + 450,
							cy + res.Size.Y/2 + 50,
						}
						// Clamp
						if cRoi[0] < 0 {
							cRoi[0] = 0
						}
						if cRoi[1] < 0 {
							cRoi[1] = 0
						}
						if cRoi[2] > 1919 {
							cRoi[2] = 1919
						}
						if cRoi[3] > 1079 {
							cRoi[3] = 1079
						}

						soldArea := m.Img.Crop(screen, cRoi)
						soldRes := m.Img.Match(soldArea, m.soldListTpl)
						if soldRes.Confidence >= threshold {
							fmt.Printf("[FRUIT] %s detected as SOLD OUT in list\n", name)
							m.checked[name] = true
							continue
						}
					}

					targetsInView = append(targetsInView, fruitTarget{
						name: name,
						pos:  image.Point{X: cx, Y: cy},
						size: res.Size,
					})
				}
			}

			// 2. Process found targets
			shouldResetAfterPurchase := false
			if len(targetsInView) > 0 {
				fmt.Printf("[FRUIT] Found %d new items in view\n", len(targetsInView))
				for _, item := range targetsInView {
					fmt.Printf("[FRUIT] Selecting %s at (%d, %d)\n", item.name, item.pos.X, item.pos.Y)
					m.ADB.Tap(item.pos.X, item.pos.Y)
					time.Sleep(1200 * time.Millisecond)

					// Detailed check in buy panel
					png2, _ := m.ADB.Screencap()
					screen2, _ := m.Img.DecodeScreenshot(png2)
					if screen2 == nil {
						continue
					}

					buyPanelRoi := m.Config.ROI.Buy
					buyArea := m.Img.Crop(screen2, buyPanelRoi)
					soldRes := m.Img.Match(buyArea, m.soldTpl)

					if soldRes.Confidence < threshold {
						// Item available for purchase
						fmt.Printf("[FRUIT] %s is AVAILABLE. Executing purchase...\n", item.name)
						m.ADB.Tap(m.Config.Buttons.Buy[0], m.Config.Buttons.Buy[1])
						time.Sleep(600 * time.Millisecond)
						m.ADB.Tap(m.Config.Buttons.MaxQty[0], m.Config.Buttons.MaxQty[1])
						time.Sleep(500 * time.Millisecond)
						m.ADB.Tap(m.Config.Buttons.Confirm[0], m.Config.Buttons.Confirm[1])

						m.bought[item.name] = true
						shouldResetAfterPurchase = true
						fmt.Printf("[FRUIT] Successfully bought %s\n", item.name)
					} else {
						fmt.Printf("[FRUIT] %s is SOLD OUT in detail panel\n", item.name)
					}

					m.checked[item.name] = true
					time.Sleep(800 * time.Millisecond)

					if shouldResetAfterPurchase {
						break
					}
				}
			}

			if shouldResetAfterPurchase {
				fmt.Println("[FRUIT] Resetting scroll position due to purchase...")
				m.scrollToTop()
				scrollCount = 0
				continue
			}

			// 3. Scroll down if still missing items
			if len(m.checked) < activeFruitsCount {
				fmt.Printf("[FRUIT] Scrolling screen (%d/%d) - Checked: %d/%d\n", scrollCount+1, maxScrolls, len(m.checked), activeFruitsCount)
				m.ADB.Swipe(600, 900, 600, 450, 300)
				time.Sleep(1500 * time.Millisecond)
				scrollCount++
			} else {
				fmt.Println("[FRUIT] All items checked.")
				break ScanLoop
			}
		}
	}

	fmt.Printf("[FRUIT] Buy Fruits Cycle Finished. Items Bought: %d\n", len(m.bought))
	m.ClosePanel()
	return nil
}

func (m *BuyFruitsModule) ClosePanel() {
	fmt.Println("[FRUIT] Closing shop panel...")
	m.ADB.Tap(m.Config.Buttons.CloseFruit1[0], m.Config.Buttons.CloseFruit1[1])
	time.Sleep(1 * time.Second)
	m.ADB.Tap(m.Config.Buttons.CloseFruit2[0], m.Config.Buttons.CloseFruit2[1])
	time.Sleep(1 * time.Second)
	// Safety extra click
	m.ADB.Tap(m.Config.Buttons.CloseFruit2[0], m.Config.Buttons.CloseFruit2[1])
}
