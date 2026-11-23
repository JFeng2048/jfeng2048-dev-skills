package {{package_name}}.core.designsystem.theme

import androidx.compose.ui.unit.dp

/**
 * 尺寸 token：8dp 栅格。
 * 页面里不要出现裸的 16.dp 这类魔法值，统一走这里。
 */
object Dimens {
    val xs = 4.dp
    val sm = 8.dp
    val md = 12.dp
    val lg = 16.dp
    val xl = 24.dp
    val xxl = 32.dp

    /** 卡片 / 图片圆角 */
    val cardRadius = 12.dp

    /** 按钮圆角 */
    val buttonRadius = 10.dp

    /** 列表缩略图 */
    val thumbSize = 72.dp

    /** 头像 */
    val avatarSize = 48.dp
}
