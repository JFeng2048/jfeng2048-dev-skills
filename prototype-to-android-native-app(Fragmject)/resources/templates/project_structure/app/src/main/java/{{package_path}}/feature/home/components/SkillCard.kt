package {{package_name}}.feature.home.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import {{package_name}}.core.designsystem.theme.AppTheme
import {{package_name}}.core.designsystem.theme.Dimens
import {{package_name}}.data.model.Skill

/**
 * 列表卡片：左图右文，标题 1 行、描述 2 行、底部作者 + 价格。
 * 远程图片必须给占位底色，避免加载期间跳动。
 */
@Composable
fun SkillCard(
    skill: Skill,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        onClick = onClick,
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(Dimens.cardRadius),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Row(modifier = Modifier.padding(Dimens.md), verticalAlignment = Alignment.Top) {
            AsyncImage(
                model = skill.avatar,
                contentDescription = skill.title,
                contentScale = ContentScale.Crop,
                modifier = Modifier
                    .size(Dimens.thumbSize)
                    .clip(RoundedCornerShape(Dimens.sm))
                    .background(MaterialTheme.colorScheme.surfaceVariant),
            )

            Spacer(modifier = Modifier.width(Dimens.md))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = skill.title,
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurface,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )

                Spacer(modifier = Modifier.height(Dimens.xs))

                Text(
                    text = skill.description,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )

                Spacer(modifier = Modifier.height(Dimens.sm))

                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = if (skill.tags.isEmpty()) "未分类" else skill.tags.take(2).joinToString(" · "),
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    Spacer(modifier = Modifier.weight(1f))
                    Text(
                        text = skill.priceText,
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
            }
        }
    }
}

@Preview(showBackground = true, widthDp = 360)
@Composable
private fun SkillCardPreview() {
    AppTheme {
        SkillCard(
            skill = Skill(
                id = "1",
                title = "可以教你吉他入门到弹唱，学期内包会",
                author = "同学1",
                avatar = "",
                tags = listOf("线下", "周末"),
                price = 0.0,
                description = "可线上或线下，时间灵活，欢迎私聊细聊。",
                createdAt = "2026-11-01",
            ),
            onClick = {},
        )
    }
}
