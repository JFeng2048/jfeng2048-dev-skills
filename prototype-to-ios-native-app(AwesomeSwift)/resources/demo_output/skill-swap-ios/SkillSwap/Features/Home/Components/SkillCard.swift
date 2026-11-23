import SwiftUI
import Kingfisher

/// 列表卡片：左图右文，标题 1 行、描述 2 行、底部作者 + 价格
struct SkillCard: View {

    let skill: Skill

    var body: some View {
        HStack(alignment: .top, spacing: AppTheme.Spacing.md) {
            KFImage(URL(string: skill.avatar))
                .placeholder {
                    Rectangle().fill(AppTheme.surface)
                }
                .resizable()
                .scaledToFill()
                .frame(width: AppTheme.Size.listThumb, height: AppTheme.Size.listThumb)
                .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.sm, style: .continuous))

            VStack(alignment: .leading, spacing: AppTheme.Spacing.xs) {
                Text(skill.title)
                    .font(.headline)
                    .foregroundStyle(AppTheme.textPrimary)
                    .lineLimit(1)

                Text(skill.detail)
                    .font(.footnote)
                    .foregroundStyle(AppTheme.textSecondary)
                    .lineLimit(2)

                HStack {
                    Text(skill.tags.isEmpty ? "—" : skill.tags.prefix(2).joined(separator: " · "))
                        .font(.caption2)
                        .foregroundStyle(AppTheme.textSecondary)

                    Spacer()

                    Text(skill.priceText)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(AppTheme.brandPrimary)
                }
            }
        }
        .cardStyle()
    }
}
