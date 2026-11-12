package np.recordo.shopping

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private data class StoreProduct(val name: String, val category: String, val priceNpr: Int, val unit: String)

private val sampleProducts = listOf(
    StoreProduct("Fresh Tomato", "Vegetables", 80, "per kg"),
    StoreProduct("Seasonal Banana", "Fruits", 140, "per dozen"),
    StoreProduct("Basmati Rice", "Groceries", 950, "5 kg bag"),
    StoreProduct("Mustard Oil", "Daily Essentials", 320, "per litre")
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { RecordoApp() }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun RecordoApp() {
    var search by remember { mutableStateOf("") }
    var selectedCategory by remember { mutableStateOf("All") }
    val categories = listOf("All", "Vegetables", "Fruits", "Groceries", "Daily Essentials")
    val filtered = sampleProducts.filter {
        (selectedCategory == "All" || it.category == selectedCategory) &&
            it.name.contains(search, ignoreCase = true)
    }

    MaterialTheme {
        Scaffold(topBar = {
            TopAppBar(title = {
                Column {
                    Text("Recordo", fontWeight = FontWeight.Bold)
                    Text("Shopping in Nepal", fontSize = 12.sp)
                }
            })
        }) { padding ->
            LazyColumn(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                item {
                    Text("Namaste! स्वागत छ", fontSize = 23.sp, fontWeight = FontWeight.Bold)
                    Text("नेपालभरिका सामान एउटै ठाउँमा", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                item {
                    OutlinedTextField(
                        value = search,
                        onValueChange = { search = it },
                        modifier = Modifier.fillMaxWidth(),
                        placeholder = { Text("Search products") },
                        leadingIcon = { Icon(Icons.Default.Search, contentDescription = "Search") },
                        singleLine = true,
                        shape = RoundedCornerShape(16.dp)
                    )
                }
                item {
                    Text("Categories", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                    Spacer(Modifier.height(8.dp))
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        categories.chunked(3).forEach { group ->
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                group.forEach { category ->
                                    FilterChip(
                                        selected = selectedCategory == category,
                                        onClick = { selectedCategory = category },
                                        label = { Text(category) }
                                    )
                                }
                            }
                        }
                    }
                }
                item {
                    Text("Popular products", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                    Text("Sample prices in Nepalese Rupees (NPR)", fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                items(filtered) { product ->
                    ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                        Row(
                            modifier = Modifier.fillMaxWidth().padding(16.dp),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Column(Modifier.weight(1f)) {
                                Text(product.name, fontWeight = FontWeight.SemiBold)
                                Text(product.category, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                Text(product.unit, fontSize = 12.sp)
                            }
                            Text("रु ${"%,d".format(product.priceNpr)}",
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.primary)
                        }
                    }
                }
                if (filtered.isEmpty()) item { Text("No products found.") }
                item {
                    Text("Demo catalogue only — ordering and payments are not enabled yet.",
                        fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}
