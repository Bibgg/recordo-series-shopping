package np.recordo.shopping
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

class MainActivity:ComponentActivity(){
 override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState);setContent{RecordoApp()}}
}
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun RecordoApp(){
 var products by remember{mutableStateOf<List<ProductDto>>(emptyList())}
 var pickupAreas by remember{mutableStateOf<List<PickupAreaDto>>(emptyList())}
 var search by remember{mutableStateOf("")}
 var category by remember{mutableStateOf("All")}
 var cart by remember{mutableStateOf<Map<String,Int>>(emptyMap())}
 var name by remember{mutableStateOf("")}
 var phone by remember{mutableStateOf("")}
 var district by remember{mutableStateOf("")}
 var municipality by remember{mutableStateOf("")}
 var ward by remember{mutableStateOf("")}
 var address by remember{mutableStateOf("")}
 var message by remember{mutableStateOf("Server जोड्दैछ…")}
 var busy by remember{mutableStateOf(false)}
 val scope= rememberCoroutineScope()
 val categories=listOf("All","Vegetables","Fruits","Groceries","Daily Essentials")
 fun load(){
  scope.launch{
   busy=true
   try{products=ApiClient.service.products();pickupAreas=ApiClient.service.pickupAreas();message=if(products.isEmpty())"अहिले सामान छैन। Admin बाट सामान थप्नुहोस्।" else "नेपालका सामान उपलब्ध छन्"}
   catch(e:Exception){message="Server जोडिएन। API URL जाँच्नुहोस्।"}
   finally{busy=false}
  }
 }
 LaunchedEffect(Unit){load()}
 val shown=products.filter{(category=="All"||it.category.equals(category,true))&&it.name.contains(search,true)}
 val selected=products.filter{(cart[it.id]?:0)>0}
 val total=selected.sumOf{it.price_npr*(cart[it.id]?:0)}
 MaterialTheme{
  Scaffold(topBar={TopAppBar(title={Column{Text("Recordo Nepal",fontWeight=FontWeight.Bold);Text("नेपालमै किनमेल र डेलिभरी",fontSize=12.sp)}})}){padding->
   LazyColumn(Modifier.fillMaxSize().padding(padding),contentPadding=PaddingValues(16.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
    item{Text("नमस्ते! स्वागत छ 🇳🇵",fontSize=23.sp,fontWeight=FontWeight.Bold);Text("आफ्नो गाउँ र नजिकका ठाउँमा सामान मगाउनुहोस्")}
    item{
     Text("Pickup Collection",fontWeight=FontWeight.Bold,fontSize=20.sp)
     Text("आफ्नो सामानको क्षेत्रअनुसार अर्डर जम्मा हुँदैछ",fontSize=12.sp,color=MaterialTheme.colorScheme.onSurfaceVariant)
     if(pickupAreas.isEmpty()){Text("अहिले Pickup क्षेत्रमा अर्डर छैन।")}
     pickupAreas.forEach{area->
      ElevatedCard(Modifier.fillMaxWidth()){
       Column(Modifier.padding(14.dp),verticalArrangement=Arrangement.spacedBy(6.dp)){
        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween){
         Text(area.pickup_area,fontWeight=FontWeight.Bold)
         AssistChip(onClick={},label={Text(if(area.ready_for_pickup)"Pickup तयार" else "जम्मा हुँदैछ")})
        }
        Text("${area.ready_orders} / ${area.target_orders} अर्डर")
        LinearProgressIndicator(progress={area.progress_percent/100f},modifier=Modifier.fillMaxWidth())
        Text(if(area.ready_for_pickup)"Pickup लक्ष्य पूरा भयो।" else "${area.remaining_orders} अर्डर बाँकी",fontSize=12.sp)
        Text("स्थिति: ${area.batch_status}",fontSize=12.sp)
       }
      }
     }
    }
    item{OutlinedTextField(search,{search=it},Modifier.fillMaxWidth(),placeholder={Text("सामान खोज्नुहोस्")},leadingIcon={Icon(Icons.Default.Search,null)},singleLine=true)}
    item{Text("श्रेणी",fontWeight=FontWeight.Bold);Column{categories.chunked(3).forEach{group->Row{group.forEach{c->FilterChip(selected=category==c,onClick={category=c},label={Text(c)})}}}}}
    item{Text(message);if(busy)LinearProgressIndicator(Modifier.fillMaxWidth());TextButton(onClick={load()}){Text("Refresh")}}
    items(shown,key={it.id}){p->
     ElevatedCard(Modifier.fillMaxWidth()){Row(Modifier.fillMaxWidth().padding(14.dp),horizontalArrangement=Arrangement.SpaceBetween){
      Column(Modifier.weight(1f)){Text(p.name,fontWeight=FontWeight.SemiBold);Text(p.category);Text("रु ${"%,d".format(p.price_npr)} / ${p.unit}");Text("स्टक: ${p.stock_quantity}")}
      Column{Button(enabled=p.stock_quantity>(cart[p.id]?:0),onClick={cart=cart+(p.id to ((cart[p.id]?:0)+1))}){Text("थप्नुहोस्")}
       if((cart[p.id]?:0)>0){Text("Qty: ${cart[p.id]}");TextButton(onClick={val n=(cart[p.id]?:0)-1;cart=if(n==0)cart-p.id else cart+(p.id to n)}){Text("घटाउनुहोस्")}}
      }
     }}
    }
    item{Text("तपाईंको Cart",fontWeight=FontWeight.Bold,fontSize=20.sp);Text("कुल: रु ${"%,d".format(total)}")}
    if(selected.isNotEmpty()){
     item{Text("डेलिभरी विवरण",fontWeight=FontWeight.Bold)}
     item{OutlinedTextField(name,{name=it},Modifier.fillMaxWidth(),label={Text("पूरा नाम")})}
     item{OutlinedTextField(phone,{phone=it},Modifier.fillMaxWidth(),label={Text("फोन नम्बर")})}
     item{OutlinedTextField(district,{district=it},Modifier.fillMaxWidth(),label={Text("जिल्ला")})}
     item{OutlinedTextField(municipality,{municipality=it},Modifier.fillMaxWidth(),label={Text("पालिका")})}
     item{OutlinedTextField(ward,{ward=it},Modifier.fillMaxWidth(),label={Text("वडा नम्बर")})}
     item{OutlinedTextField(address,{address=it},Modifier.fillMaxWidth(),label={Text("टोल र घरको ठेगाना")})}
     item{Button(enabled=!busy&&name.length>=2&&phone.length>=7&&district.length>=2&&municipality.length>=2&&ward.isNotBlank()&&address.length>=5,modifier=Modifier.fillMaxWidth(),onClick={
      scope.launch{busy=true;try{
       val result=ApiClient.service.placeOrder(OrderRequest(name.trim(),phone.trim(),district.trim(),municipality.trim(),ward.trim(),address.trim(),items=cart.map{OrderLineRequest(it.key,it.value)}))
       message="अर्डर सफल! नम्बर: ${result.order_code} — जम्मा रु ${result.total_npr}"
       cart=emptyMap();load()
      }catch(e:Exception){message="अर्डर हुन सकेन। स्टक र server जाँच्नुहोस्।"}finally{busy=false}}
     }){Text("अर्डर पठाउनुहोस् — COD")}}
    }
    item{Text("अर्डरपछि पसलले फोन गरेर पुष्टि गर्नेछ। अनलाइन भुक्तानी अहिले जोडिएको छैन।",fontSize=12.sp,color=MaterialTheme.colorScheme.onSurfaceVariant)}
   }
  }
 }
}
