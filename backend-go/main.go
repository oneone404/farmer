package main

import (
	"encoding/json"
	"farmer-backend-go/core"
	"farmer-backend-go/modules"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"sync"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true
	},
}

// ========== State ==========
type WorkerState struct {
	workers   map[string]*exec.Cmd
	wsClients []*websocket.Conn
	mutex     sync.RWMutex
}

var state = &WorkerState{
	workers:   make(map[string]*exec.Cmd),
	wsClients: []*websocket.Conn{},
}

func (s *WorkerState) broadcast(msg map[string]string) {
	s.mutex.RLock()
	defer s.mutex.RUnlock()
	data, _ := json.Marshal(msg)
	for _, ws := range s.wsClients {
		ws.WriteMessage(websocket.TextMessage, data)
	}
}

// ========== LDPlayer Manager ==========
func getADBDevices(adbPath string) []string {
	cmd := exec.Command(adbPath, "devices")
	out, err := cmd.Output()
	if err != nil {
		return []string{}
	}
	lines := strings.Split(string(out), "\n")
	devices := []string{}
	for _, line := range lines[1:] {
		if strings.Contains(line, "device") && !strings.Contains(line, "offline") {
			parts := strings.Fields(line)
			if len(parts) > 0 {
				devices = append(devices, parts[0])
			}
		}
	}
	return devices
}

func getLDInstances(ldPath string, adbPath string) []map[string]interface{} {
	ldConsole := filepath.Join(ldPath, "ldconsole.exe")
	if _, err := os.Stat(ldConsole); os.IsNotExist(err) {
		fmt.Println("[LD] ldconsole.exe not found at", ldConsole)
		return []map[string]interface{}{}
	}

	cmd := exec.Command(ldConsole, "list2")
	out, err := cmd.Output()
	if err != nil {
		return []map[string]interface{}{}
	}

	adbDevices := getADBDevices(adbPath)
	instances := []map[string]interface{}{}

	lines := strings.Split(string(out), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		parts := strings.Split(line, ",")
		if len(parts) < 2 {
			continue
		}
		idx, err := strconv.Atoi(parts[0])
		if err != nil || idx >= 1000 {
			continue
		}

		name := parts[1]
		running := isLDRunning(ldConsole, idx)
		serial := ""
		if running {
			serial = mapLDToSerial(idx, adbDevices)
		}

		instances = append(instances, map[string]interface{}{
			"index":   idx,
			"name":    name,
			"running": running,
			"serial":  serial,
			"status":  "idle",
		})
	}
	return instances
}

func isLDRunning(ldConsole string, index int) bool {
	cmd := exec.Command(ldConsole, "isrunning", "--index", strconv.Itoa(index))
	out, _ := cmd.Output()
	return strings.Contains(strings.ToLower(string(out)), "running")
}

func mapLDToSerial(index int, adbDevices []string) string {
	consolePort := 5554 + (index * 2)
	adbPort := 5555 + (index * 2)

	emulatorSerial := fmt.Sprintf("emulator-%d", consolePort)
	for _, d := range adbDevices {
		if d == emulatorSerial {
			return emulatorSerial
		}
	}

	ipSerial := fmt.Sprintf("127.0.0.1:%d", adbPort)
	for _, d := range adbDevices {
		if d == ipSerial {
			return ipSerial
		}
	}
	return ""
}

// ========== Main ==========
func main() {
	r := gin.Default()
	r.Use(cors.Default())

	cfg := core.NewConfig()
	imgProc := core.NewImageProcessor(0.9)

	ldPath := cfg.GlobalConfig.LDPlayerPath
	if ldPath == "" {
		ldPath = `C:\LDPlayer\LDPlayer9`
	}
	adbPath := cfg.GlobalConfig.ADBPath
	if adbPath == "" {
		adbPath = "adb.exe"
	}

	// ========== API Routes ==========
	r.GET("/status", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "online", "backend": "go"})
	})

	r.GET("/devices", func(c *gin.Context) {
		instances := getLDInstances(ldPath, adbPath)
		result := []map[string]interface{}{}
		for _, inst := range instances {
			if inst["running"].(bool) && inst["serial"].(string) != "" {
				result = append(result, inst)
			}
		}
		c.JSON(200, result)
	})

	r.GET("/fruits", func(c *gin.Context) {
		c.JSON(200, cfg.GetFruits())
	})

	r.GET("/config/:index", func(c *gin.Context) {
		// Return default config for now
		c.JSON(200, gin.H{
			"enable_buy_fruits":         true,
			"enable_buy_voi":            true,
			"enable_harvest_sell":       true,
			"use_time_gate":             true,
			"first_run_immediate":       true,
			"threshold":                 0.95,
			"harvest_sell_cycles":       1,
			"sell_cycles_after_harvest": 1,
			"fruits":                    map[string]interface{}{},
		})
	})

	r.POST("/config/:index", func(c *gin.Context) {
		// TODO: Save config
		c.JSON(200, gin.H{"status": "ok"})
	})

	r.POST("/worker/start", func(c *gin.Context) {
		var req struct {
			DeviceSerial string `json:"device_serial"`
			LDIndex      int    `json:"ld_index"`
		}
		if err := c.BindJSON(&req); err != nil {
			c.JSON(400, gin.H{"status": "error", "message": err.Error()})
			return
		}

		state.mutex.Lock()
		if _, exists := state.workers[req.DeviceSerial]; exists {
			state.mutex.Unlock()
			c.JSON(400, gin.H{"status": "error", "message": "Worker already running"})
			return
		}
		state.mutex.Unlock()

		// Start worker goroutine
		go func() {
			adb := core.NewADBController(adbPath, req.DeviceSerial)
			buyModule := modules.NewBuyFruitsModule(adb, imgProc, cfg)

			state.broadcast(map[string]string{
				"type":          "log",
				"device_serial": req.DeviceSerial,
				"message":       "Worker started",
			})

			err := buyModule.Run()
			if err != nil {
				state.broadcast(map[string]string{
					"type":          "log",
					"device_serial": req.DeviceSerial,
					"message":       fmt.Sprintf("Error: %v", err),
				})
			}

			state.broadcast(map[string]string{
				"type":          "worker_stopped",
				"device_serial": req.DeviceSerial,
			})
		}()

		c.JSON(200, gin.H{"status": "ok"})
	})

	r.POST("/worker/stop/:serial", func(c *gin.Context) {
		serial := c.Param("serial")
		state.mutex.Lock()
		if cmd, exists := state.workers[serial]; exists {
			cmd.Process.Kill()
			delete(state.workers, serial)
		}
		state.mutex.Unlock()

		state.broadcast(map[string]string{
			"type":          "worker_stopped",
			"device_serial": serial,
		})

		c.JSON(200, gin.H{"status": "ok"})
	})

	// WebSocket
	r.GET("/ws", func(c *gin.Context) {
		ws, err := upgrader.Upgrade(c.Writer, c.Request, nil)
		if err != nil {
			return
		}
		defer ws.Close()

		state.mutex.Lock()
		state.wsClients = append(state.wsClients, ws)
		state.mutex.Unlock()

		for {
			_, message, err := ws.ReadMessage()
			if err != nil {
				break
			}
			if string(message) == `{"type":"ping"}` {
				ws.WriteMessage(websocket.TextMessage, []byte(`{"type":"pong"}`))
			}
		}

		// Remove client on disconnect
		state.mutex.Lock()
		for i, client := range state.wsClients {
			if client == ws {
				state.wsClients = append(state.wsClients[:i], state.wsClients[i+1:]...)
				break
			}
		}
		state.mutex.Unlock()
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8765"
	}

	fmt.Printf("Go Backend starting on port %s...\n", port)
	r.Run(":" + port)
}
