# Coupons & Events tab · tile images

Standard background images for the **Events** and **Coupons** filter tiles in the Coupons & Events tab (CE1). They replace a video thumbnail.

| | |
|---|---|
| Size | 144 × 96 pt (3:2). The tile is 97–121 × 72 pt, so draw the image center-cropped: `centerCrop` (Android), `scaleAspectFill` / `.fill` (iOS). The art stays inside the crop at every phone size. |
| Android | `android/drawable-*/tile_events.webp`, `tile_coupons.webp`: WebP quality 90, mdpi → xxxhdpi (144 × 96 → 576 × 384 px), 2–9 KB each. Copy into `res/`. |
| iOS | `ios/TileEvents.imageset`, `ios/TileCoupons.imageset`: PNG @2x and @3x with `Contents.json`. Drag into `Assets.xcassets`. |
| Master | `svg/*.svg`: the vector source, about 3 KB. Uses only paths, gradients and transforms, so it can be converted to an Android VectorDrawable or an Xcode vector asset if you prefer vector. |
| From a server | Serve the xxhdpi WebP (432 × 288 px, about 6 KB). |

Rules:
- The images are opaque with square corners. The app rounds the tile (radius 13), adds the bottom gradient (46 pt, transparent → black 70 %), and draws the label and the count.
- There is no text in the images, so they work in every language.
- White label contrast over the label area is at least 7.5 : 1 at every tile size.
