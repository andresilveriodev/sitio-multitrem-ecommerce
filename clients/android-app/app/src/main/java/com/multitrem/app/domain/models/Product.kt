package com.multitrem.app.domain.models

data class Product(
    val id: Long = 0,
    val name: String,
    val description: String? = null,
    val price: Double,
    val active: Boolean = true
)
