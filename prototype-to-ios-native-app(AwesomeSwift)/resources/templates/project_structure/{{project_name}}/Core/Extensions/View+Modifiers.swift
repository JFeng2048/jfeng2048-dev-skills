import SwiftUI

extension View {

    /// 卡片容器样式：圆角 + 表面色 + 轻阴影
    func cardStyle() -> some View {
        self
            .padding(AppTheme.Spacing.md)
            .background(AppTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous))
            .shadow(color: Color.black.opacity(0.05), radius: 4, y: 2)
    }

    /// 输入框样式：表面色背景 + 小圆角 + 内边距
    func inputStyle() -> some View {
        self
            .padding(AppTheme.Spacing.md)
            .background(AppTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.sm, style: .continuous))
    }
}
