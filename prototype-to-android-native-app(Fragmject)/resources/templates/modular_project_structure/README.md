# {{project_name}}

{{app_name}} - native Android multi-module starter.

## Modules

```text
:app
├── :core:*                       # shared platform capabilities
└── :feature:<domain>:impl
    └── :feature:<domain>:api
```

`app` is the composition root. `core` does not depend on feature modules. A feature implementation may depend on its own API, required core modules, and other feature APIs; it must not depend on another feature implementation.

The generated `FeatureHomeScreen` is a small scaffold. Replace it with the screens, state, and interactions derived from the supplied prototype. Add platform components only when that feature requires them.

## Version policy

Versions in `gradle/libs.versions.toml` were resolved for this project at generation time from official release and compatibility information. The catalog intentionally records concrete versions so builds remain reproducible. Upgrade the toolchain as a compatible set.

Resolution checked: {{versions_checked_at}}

Sources: {{versions_sources}}

## Run

1. Open this directory in Android Studio and sync Gradle.
2. Set `sdk.dir` in `local.properties`, or configure the Android SDK in Android Studio.
3. Run the `app` configuration on a compatible emulator or device.

Command line:

```bash
gradle -p . validateArchitecture
gradle -p . :app:assembleDebug
gradle -p . test
```

The source template does not bundle Gradle wrapper launch scripts or the wrapper JAR. With a compatible local Gradle installation, generate them using `gradle -p . wrapper --gradle-version {{gradle_version}} --distribution-type bin`; then use `./gradlew` (or `gradlew.bat` on Windows).

## Add a feature

1. Create `feature/<domain>/api` and `feature/<domain>/impl`.
2. Add both modules to `settings.gradle.kts` and add the implementation to app composition.
3. Put cross-module route/parameter contracts in `api`; register the destination in `impl`.
4. Keep repositories, DTOs, entities, and UI implementations inside their owning feature.
5. Check the dependency graph and merged manifest after adding Android components.
