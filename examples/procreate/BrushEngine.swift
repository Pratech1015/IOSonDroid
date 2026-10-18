import UIKit
import CoreGraphics

// Procreate Brush & Pressure Point Model
struct BrushStrokePoint {
    let location: CGPoint
    let pressure: CGFloat
    let tilt: Float
    let azimuth: Float
    let timestamp: Double
}

struct ProcreateBrush {
    let name: String
    let diameter: Float
    let spacing: Float
    let opacity: Float
    let color: UIColor
}

struct CanvasLayer {
    let layerId: String
    var name: String
    var opacity: Float
    var isVisible: Bool
}

// Procreate Canvas Drawing Engine
class CanvasDrawingEngine {
    var activeBrush: ProcreateBrush?
    var layers: [CanvasLayer] = []
    var activePoints: [BrushStrokePoint] = []

    func renderStroke(point: BrushStrokePoint, context: CGContext) -> Bool {
        guard let brush = activeBrush else { return false }
        print("Rendering \(brush.name) stroke at (\(point.location.x), \(point.location.y)) with pressure \(point.pressure)")
        return true
    }

    func addLayer(name: String) -> CanvasLayer {
        let newLayer = CanvasLayer(layerId: "layer_\(layers.count + 1)", name: name, opacity: 1.0, isVisible: true)
        layers.append(newLayer)
        return newLayer
    }
}
