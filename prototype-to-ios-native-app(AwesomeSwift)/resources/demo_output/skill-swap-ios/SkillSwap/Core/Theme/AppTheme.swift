import SwiftUI

/// 设计 token
///
/// 颜色来自 `Assets.xcassets`（每个 colorset 内配置浅色/深色两套），
/// 页面里只用这里的语义常量，禁止 `Color(red:green:blue:)`。
enum AppTheme {

    // MARK: - 语义色

    static let brandPrimary = Color("BrandPrimary")
    static let background = Color("AppBackground")
    static let surface = Color("Surface")
    static let textPrimary = Color("TextPrimary")
    static let textSecondary = Color("TextSecondary")
    static let separator = Color("Separator")

    // MARK: - 间距（8pt 栅格）

    enum Spacing {
        static let xs: CGFloat = 4
        static let sm: CGFloat = 8
        static let md: CGFloat = 12
        static let lg: CGFloat = 16
        static let xl: CGFloat = 24
        static let xxl: CGFloat = 32
    }

    // MARK: - 圆角

    enum Radius {
        static let sm: CGFloat = 8
        static let md: CGFloat = 12
        static let lg: CGFloat = 20
    }

    // MARK: - 尺寸

    enum Size {
        static let listThumb: CGFloat = 72
        static let avatar: CGFloat = 48
        static let detailHero: CGFloat = 200
    }
}
