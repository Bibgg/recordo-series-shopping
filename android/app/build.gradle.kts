plugins {
 id("com.android.application")
 id("org.jetbrains.kotlin.android")
 id("org.jetbrains.kotlin.plugin.compose")
}
val apiBaseUrl=providers.gradleProperty("API_BASE_URL").orElse("http://10.0.2.2:8000/").get()
android {\n compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }\n kotlinOptions { jvmTarget = "17" }
 namespace="np.recordo.shopping"
 compileSdk=35
 defaultConfig {
  applicationId="np.recordo.shopping"
  minSdk=24
  targetSdk=35
  versionCode=2
  versionName="0.2.0"
  buildConfigField("String","API_BASE_URL","\"$apiBaseUrl\"")
 }
 buildFeatures { compose=true; buildConfig=true }
}
dependencies {
 implementation(platform("androidx.compose:compose-bom:2024.12.01"))
 implementation("androidx.activity:activity-compose:1.9.3")
 implementation("androidx.compose.ui:ui")
 implementation("androidx.compose.ui:ui-tooling-preview")
 implementation("androidx.compose.material3:material3")
 implementation("androidx.compose.material:material-icons-extended")
 implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
 implementation("com.squareup.retrofit2:retrofit:2.11.0")
 implementation("com.squareup.retrofit2:converter-gson:2.11.0")
 debugImplementation("androidx.compose.ui:ui-tooling")
}
