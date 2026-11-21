package com.bigico.marketplace

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.text.NumberFormat
import java.util.Locale

private val BigicoBlue = Color(0xFF175CD3)
private val BigicoInk = Color(0xFF152238)
private val BigicoBackground = Color(0xFFF5F7FB)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(colorScheme = lightColorScheme(
                primary = BigicoBlue, background = BigicoBackground,
                surface = Color.White, onBackground = BigicoInk, onSurface = BigicoInk
            )) { BigicoApp() }
        }
    }
}

private data class Product(
    val id: String, val name: String, val description: String,
    val category: String, val priceNpr: Int, val unit: String, val stockQuantity: Int
)

private val categories = listOf("सबै", "खाद्य", "हस्तकला", "कपडा", "कृषि")

@Composable
private fun BigicoApp() {
    val scope = rememberCoroutineScope()
    var products by remember { mutableStateOf(emptyList<Product>()) }
    var loading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var search by remember { mutableStateOf("") }
    var selectedCategory by remember { mutableStateOf("सबै") }
    var selectedTab by remember { mutableStateOf(0) }
    val apiBaseUrl = BuildConfig.API_BASE_URL.trim().trimEnd('/')

    suspend fun refreshProducts() {
        if (apiBaseUrl.isBlank()) {
            errorMessage = "उत्पादन देखाउन पहिले BIGICO API सर्भर जोड्नुपर्छ।"
            products = emptyList()
            return
        }
        loading = true
        errorMessage = null
        try {
            products = withContext(Dispatchers.IO) { fetchProducts(apiBaseUrl) }
        } catch (error: Exception) {
            errorMessage = error.message ?: "सर्भरसँग जडान हुन सकेन।"
        } finally {
            loading = false
        }
    }

    LaunchedEffect(apiBaseUrl) { refreshProducts() }

    val visibleProducts = products.filter { product ->
        val matchesSearch = search.isBlank() ||
            product.name.contains(search, ignoreCase = true) ||
            product.description.contains(search, ignoreCase = true)
        val categoryText = product.category.lowercase(Locale.ROOT)
        val matchesCategory = when (selectedCategory) {
            "खाद्य" -> listOf("food", "grocery", "खाद्य", "अन्न").any(categoryText::contains)
            "हस्तकला" -> listOf("craft", "handicraft", "हस्तकला").any(categoryText::contains)
            "कपडा" -> listOf("cloth", "textile", "कपडा").any(categoryText::contains)
            "कृषि" -> listOf("farm", "agri", "कृषि", "vegetable", "fruit").any(categoryText::contains)
            else -> true
        }
        matchesSearch && matchesCategory
    }

    Scaffold(
        containerColor = BigicoBackground,
        bottomBar = {
            NavigationBar(containerColor = Color.White) {
                NavigationBarItem(selectedTab == 0, { selectedTab = 0 }, icon = { Text("⌂", fontSize = 22.sp) }, label = { Text("गृह") })
                NavigationBarItem(selectedTab == 1, { selectedTab = 1 }, icon = { Text("▦", fontSize = 20.sp) }, label = { Text("श्रेणी") })
                NavigationBarItem(selectedTab == 2, { selectedTab = 2 }, icon = { Text("▤", fontSize = 20.sp) }, label = { Text("अर्डर") })
                NavigationBarItem(selectedTab == 3, { selectedTab = 3 }, icon = { Text("●", fontSize = 20.sp) }, label = { Text("प्रोफाइल") })
            }
        }
    ) { innerPadding ->
        if (selectedTab == 2 || selectedTab == 3) {
            ComingSoonScreen(if (selectedTab == 2) "मेरो अर्डर" else "मेरो प्रोफाइल", Modifier.padding(innerPadding))
        } else {
            Column(Modifier.fillMaxSize().padding(innerPadding)) {
                Column(Modifier.fillMaxWidth().background(Color.White).padding(horizontal = 20.dp, vertical = 18.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(Modifier.size(44.dp).background(BigicoBlue, RoundedCornerShape(14.dp)), contentAlignment = Alignment.Center) {
                            Text("B", color = Color.White, fontSize = 26.sp, fontWeight = FontWeight.Black)
                        }
                        Spacer(Modifier.width(11.dp))
                        Column(Modifier.weight(1f)) {
                            Text("BIGICO", fontSize = 23.sp, fontWeight = FontWeight.ExtraBold, color = BigicoInk)
                            Text("बागलुङको स्थानीय बजार", fontSize = 12.sp, color = Color(0xFF667085))
                        }
                        Surface(shape = CircleShape, color = Color(0xFFEAF2FF)) {
                            Text("🇳🇵", Modifier.padding(9.dp), fontSize = 18.sp)
                        }
                    }
                    Spacer(Modifier.height(18.dp))
                    Text("स्थानीय उत्पादन, आफ्नै बजारमा", fontSize = 21.sp, fontWeight = FontWeight.Bold, color = BigicoInk)
                    Text("बागलुङका उत्पादक र ग्राहकलाई जोड्दै", fontSize = 13.sp, color = Color(0xFF667085))
                    Spacer(Modifier.height(14.dp))
                    OutlinedTextField(
                        value = search, onValueChange = { search = it },
                        modifier = Modifier.fillMaxWidth(), singleLine = true,
                        shape = RoundedCornerShape(14.dp),
                        placeholder = { Text("उत्पादन खोज्नुहोस्...") },
                        leadingIcon = { Text("⌕", fontSize = 22.sp) }
                    )
                }

                Row(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 10.dp), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    categories.forEach { category ->
                        AssistChip(
                            onClick = { selectedCategory = category; selectedTab = 0 },
                            label = { Text(category, fontSize = 11.sp, fontWeight = if (selectedCategory == category) FontWeight.Bold else FontWeight.Normal) },
                            shape = RoundedCornerShape(12.dp)
                        )
                    }
                }

                Row(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text("स्थानीय उत्पादन", fontSize = 17.sp, fontWeight = FontWeight.Bold, color = BigicoInk)
                    Spacer(Modifier.weight(1f))
                    TextButton(onClick = { scope.launch { refreshProducts() } }, enabled = !loading) {
                        Text(if (loading) "लोड हुँदैछ" else "↻ रिफ्रेस", color = BigicoBlue, fontSize = 12.sp)
                    }
                }

                when {
                    loading && products.isEmpty() -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator(color = BigicoBlue)
                    }
                    visibleProducts.isEmpty() -> EmptyProducts(
                        errorMessage ?: "अहिलेसम्म उत्पादन सूचीबद्ध गरिएको छैन।",
                        onRetry = { scope.launch { refreshProducts() } }
                    )
                    else -> LazyVerticalGrid(
                        columns = GridCells.Fixed(2), modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(start = 14.dp, end = 14.dp, top = 8.dp, bottom = 18.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) { items(visibleProducts, key = { it.id }) { ProductCard(it) } }
                }
            }
        }
    }
}

@Composable
private fun ProductCard(product: Product) {
    Card(
        modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Column(Modifier.padding(12.dp)) {
            Box(Modifier.fillMaxWidth().height(104.dp).background(Color(0xFFEAF2FF), RoundedCornerShape(13.dp)), contentAlignment = Alignment.Center) {
                Text(categoryEmoji(product.category), fontSize = 43.sp)
            }
            Spacer(Modifier.height(10.dp))
            Text(product.name, fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = BigicoInk, maxLines = 2, overflow = TextOverflow.Ellipsis)
            Text(product.category, fontSize = 11.sp, color = Color(0xFF667085), maxLines = 1)
            Spacer(Modifier.height(7.dp))
            Text(NprFormatter.format(product.priceNpr), fontSize = 16.sp, fontWeight = FontWeight.Bold, color = BigicoBlue)
            Text("प्रति ${product.unit} • स्टक ${product.stockQuantity}", fontSize = 10.sp, color = Color(0xFF667085))
        }
    }
}

@Composable
private fun EmptyProducts(message: String, onRetry: () -> Unit) {
    Box(Modifier.fillMaxSize().padding(28.dp), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text("🧺", fontSize = 52.sp)
            Spacer(Modifier.height(12.dp))
            Text("BIGICO बजार तयार हुँदैछ", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = BigicoInk)
            Spacer(Modifier.height(7.dp))
            Text(message, fontSize = 13.sp, color = Color(0xFF667085))
            Spacer(Modifier.height(16.dp))
            Button(onClick = onRetry) { Text("फेरि प्रयास गर्नुहोस्") }
        }
    }
}

@Composable
private fun ComingSoonScreen(title: String, modifier: Modifier = Modifier) {
    Box(modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text("BIGICO", fontSize = 26.sp, fontWeight = FontWeight.ExtraBold, color = BigicoBlue)
            Spacer(Modifier.height(10.dp))
            Text(title, fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Text("यो सुविधा अर्को संस्करणमा थपिनेछ।", color = Color(0xFF667085), fontSize = 13.sp)
        }
    }
}

private fun categoryEmoji(category: String): String {
    val value = category.lowercase(Locale.ROOT)
    return when {
        listOf("honey", "food", "grocery", "खाद्य").any(value::contains) -> "🍯"
        listOf("craft", "handicraft", "हस्तकला").any(value::contains) -> "🧺"
        listOf("cloth", "textile", "कपडा").any(value::contains) -> "🧣"
        listOf("farm", "agri", "fruit", "vegetable", "कृषि").any(value::contains) -> "🌾"
        else -> "📦"
    }
}

private fun fetchProducts(baseUrl: String): List<Product> {
    val connection = URL("$baseUrl/api/v1/products").openConnection() as HttpURLConnection
    connection.requestMethod = "GET"
    connection.connectTimeout = 10_000
    connection.readTimeout = 15_000
    connection.setRequestProperty("Accept", "application/json")
    try {
        val status = connection.responseCode
        if (status !in 200..299) throw IOException("सर्भरले अनुरोध स्वीकार गरेन (HTTP $status)")
        val body = connection.inputStream.bufferedReader().use { it.readText() }
        val json = JSONArray(body)
        return buildList {
            for (index in 0 until json.length()) {
                val item = json.getJSONObject(index)
                add(Product(
                    id = item.optString("id"),
                    name = item.optString("name", "Unnamed product"),
                    description = item.optString("description", ""),
                    category = item.optString("category", "अन्य"),
                    priceNpr = item.optInt("price_npr", 0),
                    unit = item.optString("unit", "piece"),
                    stockQuantity = item.optInt("stock_quantity", 0)
                ))
            }
        }
    } finally {
        connection.disconnect()
    }
}

object NprFormatter {
    fun format(amount: Int): String {
        val formatted = NumberFormat.getIntegerInstance(Locale.US).format(amount.coerceAtLeast(0))
        return "रु $formatted"
    }
}
