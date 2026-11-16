package org.jellyfin.androidtv.ui.composable

import androidx.annotation.DrawableRes
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.graphics.FilterQuality
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.imageResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntSize
import kotlin.math.roundToInt

/**
 * Draws a pixel-art drawable (place it in drawable-nodpi) at the largest whole-number scale that keeps
 * it within [maxHeight], without filtering, so every art pixel stays a crisp square. When the parent
 * constrains the layout smaller than the scaled image, the image is drawn centred and may overflow.
 */
@Composable
fun PixelArtImage(
	@DrawableRes id: Int,
	contentDescription: String?,
	maxHeight: Dp,
	modifier: Modifier = Modifier,
) {
	val bitmap = ImageBitmap.imageResource(id)
	val density = LocalDensity.current
	val scale = maxOf(1, with(density) { maxHeight.roundToPx() } / bitmap.height)
	val width = bitmap.width * scale
	val height = bitmap.height * scale

	Spacer(
		modifier = modifier
			.size(with(density) { width.toDp() }, with(density) { height.toDp() })
			.semantics { if (contentDescription != null) this.contentDescription = contentDescription }
			.drawBehind {
				drawImage(
					image = bitmap,
					dstOffset = IntOffset(((size.width - width) / 2).roundToInt(), ((size.height - height) / 2).roundToInt()),
					dstSize = IntSize(width, height),
					filterQuality = FilterQuality.None,
				)
			}
	)
}
