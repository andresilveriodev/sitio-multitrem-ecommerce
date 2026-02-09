# Add project specific ProGuard rules here.
# You can control the set of applied configuration files using the
# proguardFiles setting in build.gradle.

# Keep AppAuth classes
-keep class net.openid.appauth.** { *; }

# Keep Room classes
-keep class * extends androidx.room.RoomDatabase
-keep @androidx.room.Entity class *
-keep class * extends androidx.room.RoomDatabase

# Keep data classes
-keep class com.multitrem.app.data.** { *; }
-keep class com.multitrem.app.domain.** { *; }
