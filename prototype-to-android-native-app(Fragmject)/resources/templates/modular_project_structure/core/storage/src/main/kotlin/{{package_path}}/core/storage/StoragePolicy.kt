package {{package_name}}.core.storage

data class StoragePolicy(
    val schemaVersion: Int,
    val destructiveMigrationAllowed: Boolean = false,
) {
    init {
        require(schemaVersion > 0)
    }
}
