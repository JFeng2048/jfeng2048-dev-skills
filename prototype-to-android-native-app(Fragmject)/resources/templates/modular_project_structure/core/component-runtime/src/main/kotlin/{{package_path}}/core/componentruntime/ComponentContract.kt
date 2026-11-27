package {{package_name}}.core.componentruntime

data class ComponentContract(
    val owner: String,
    val exported: Boolean = false,
) {
    init {
        require(owner.isNotBlank())
    }
}
