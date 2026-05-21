package core

import (
	"fmt"
	"os/exec"
	"strconv"
)

type ADBController struct {
	ADBPath string
	Serial  string
}

func NewADBController(adbPath string, serial string) *ADBController {
	fmt.Printf("[ADB] Initialized with path=%s, serial=%s\n", adbPath, serial)
	return &ADBController{
		ADBPath: adbPath,
		Serial:  serial,
	}
}

func (a *ADBController) run(args ...string) ([]byte, error) {
	fullArgs := append([]string{"-s", a.Serial}, args...)
	cmd := exec.Command(a.ADBPath, fullArgs...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("[ADB] Command failed: %s %v\n", a.ADBPath, fullArgs)
		fmt.Printf("[ADB] Error: %v\n", err)
		fmt.Printf("[ADB] Output: %s\n", string(out))
	}
	return out, err
}

func (a *ADBController) Screencap() ([]byte, error) {
	return a.run("exec-out", "screencap", "-p")
}

func (a *ADBController) Tap(x, y int) error {
	_, err := a.run("shell", "input", "tap", strconv.Itoa(x), strconv.Itoa(y))
	return err
}

func (a *ADBController) Swipe(x1, y1, x2, y2, duration int) error {
	_, err := a.run("shell", "input", "swipe",
		strconv.Itoa(x1), strconv.Itoa(y1),
		strconv.Itoa(x2), strconv.Itoa(y2),
		strconv.Itoa(duration))
	return err
}
