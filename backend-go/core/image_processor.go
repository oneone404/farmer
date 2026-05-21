package core

import (
	"bytes"
	"fmt"
	"image"
	"image/draw"
	_ "image/png"
	"math"
	"os"

	"github.com/disintegration/imaging"
)

type MatchResult struct {
	Confidence float64
	Point      image.Point
	Size       image.Point
}

type ImageProcessor struct {
	Threshold float64
}

func NewImageProcessor(threshold float64) *ImageProcessor {
	return &ImageProcessor{Threshold: threshold}
}

func (ip *ImageProcessor) DecodeScreenshot(pngBytes []byte) (image.Image, error) {
	if len(pngBytes) == 0 {
		return nil, fmt.Errorf("empty bytes")
	}
	return imaging.Decode(bytes.NewReader(pngBytes))
}

// Fix: imaging.Decode needs a reader. strings.NewReader is bad for binary.
// Using bytes.NewReader instead. (Will update imports in write_to_file)

func (ip *ImageProcessor) Crop(img image.Image, roi []int) image.Image {
	if len(roi) != 4 || img == nil {
		return img
	}
	// roi = [x1, y1, x2, y2]
	rect := image.Rect(roi[0], roi[1], roi[2], roi[3])
	return imaging.Crop(img, rect)
}

func (ip *ImageProcessor) LoadTemplate(path string) (image.Image, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return imaging.Decode(f)
}

func (ip *ImageProcessor) toGray(img image.Image) *image.Gray {
	if g, ok := img.(*image.Gray); ok {
		return g
	}
	bounds := img.Bounds()
	gray := image.NewGray(bounds)
	draw.Draw(gray, bounds, img, bounds.Min, draw.Src)
	return gray
}

// Match performs template matching.
// Improved: Uses RGB average SAD for better accuracy than pure grayscale.
func (ip *ImageProcessor) Match(scene image.Image, template image.Image) MatchResult {
	if scene == nil || template == nil {
		return MatchResult{}
	}

	sBounds := scene.Bounds()
	tBounds := template.Bounds()
	sw, sh := sBounds.Dx(), sBounds.Dy()
	tw, th := tBounds.Dx(), tBounds.Dy()

	if sw < tw || sh < th {
		return MatchResult{}
	}

	// We'll use RGB comparisons. It's slower but much more accurate than grayscale SAD.
	// To speed up, we convert both to RGBA if they aren't.
	sRgba := ip.toRGBA(scene)
	tRgba := ip.toRGBA(template)

	bestScore := math.MaxFloat64
	var bestPoint image.Point

	// Optimization: Skip pixels to speed up initial search if needed,
	// but here we keep it simple for accuracy.
	for y := 0; y <= sh-th; y++ {
		for x := 0; x <= sw-tw; x++ {
			var sad float64
			earlyExit := false

			for ty := 0; ty < th; ty++ {
				for tx := 0; tx < tw; tx++ {
					// Get pixel from scene at relative (x+tx, y+ty)
					// Note: RGBA.Pix is [R, G, B, A, R, G, B, A, ...]
					sIdx := sRgba.PixOffset(sRgba.Rect.Min.X+x+tx, sRgba.Rect.Min.Y+y+ty)
					tIdx := tRgba.PixOffset(tRgba.Rect.Min.X+tx, tRgba.Rect.Min.Y+ty)

					// Compare R, G, B channels
					for c := 0; c < 3; c++ {
						diff := int(sRgba.Pix[sIdx+c]) - int(tRgba.Pix[tIdx+c])
						if diff < 0 {
							diff = -diff
						}
						sad += float64(diff)
					}

					if sad > bestScore {
						earlyExit = true
						break
					}
				}
				if earlyExit {
					break
				}
			}

			if sad < bestScore {
				bestScore = sad
				bestPoint = image.Point{X: x, Y: y}
			}
		}
	}

	// Max possible SAD is 255 * 3 channels * width * height
	maxSad := 255.0 * 3.0 * float64(tw) * float64(th)
	confidence := 1.0 - (bestScore / maxSad)
	if confidence < 0 {
		confidence = 0
	}

	// Log result for debugging
	if confidence > 0.8 {
		fmt.Printf("[IMG] Match found at (%d, %d) conf: %.2f\n", bestPoint.X, bestPoint.Y, confidence)
	}

	return MatchResult{
		Confidence: confidence,
		Point:      bestPoint,
		Size:       image.Point{X: tw, Y: th},
	}
}

func (ip *ImageProcessor) toRGBA(img image.Image) *image.RGBA {
	if rgba, ok := img.(*image.RGBA); ok {
		return rgba
	}
	bounds := img.Bounds()
	rgba := image.NewRGBA(bounds)
	draw.Draw(rgba, bounds, img, bounds.Min, draw.Src)
	return rgba
}
