package {{package_name}}.feature.{{domain}}.impl.di

import {{package_name}}.core.router.FeatureEntry
import {{package_name}}.feature.{{domain}}.impl.{{domain_pascal}}FeatureEntry
import dagger.Binds
import dagger.Module
import dagger.multibindings.IntoSet
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent

@Module
@InstallIn(SingletonComponent::class)
abstract class FeatureModule {
    @Binds
    @IntoSet
    abstract fun bindFeatureEntry(entry: {{domain_pascal}}FeatureEntry): FeatureEntry
}
