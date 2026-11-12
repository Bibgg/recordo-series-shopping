package np.recordo.shopping
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
data class ProductDto(val id:String,val name:String,val description:String="",val category:String,val price_npr:Int,val currency:String="NPR",val unit:String,val stock_quantity:Int,val pickup_area:String="Baglung")
data class OrderLineRequest(val product_id:String,val quantity:Int)
data class OrderRequest(val customer_name:String,val phone:String,val district:String,val municipality:String,val ward:String,val delivery_address:String,val delivery_note:String="",val items:List<OrderLineRequest>)
data class OrderResponse(val order_code:String,val status:String,val total_npr:Int,val currency:String)
data class PickupAreaDto(val pickup_area:String,val ready_orders:Int,val target_orders:Int,val remaining_orders:Int,val progress_percent:Int,val ready_for_pickup:Boolean,val batch_code:String?,val batch_status:String)
interface RecordoApi {
 @GET("api/v1/products") suspend fun products():List<ProductDto>
 @GET("api/v1/pickup/areas") suspend fun pickupAreas():List<PickupAreaDto>
 @POST("api/v1/orders") suspend fun placeOrder(@Body request:OrderRequest):OrderResponse
}
object ApiClient {
 val service:RecordoApi by lazy {
  Retrofit.Builder().baseUrl(BuildConfig.API_BASE_URL)
   .addConverterFactory(GsonConverterFactory.create()).build().create(RecordoApi::class.java)
 }
}
