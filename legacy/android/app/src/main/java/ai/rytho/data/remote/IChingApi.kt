package ai.rytho.data.remote

import retrofit2.http.POST

data class IChingHexagramData(
    val hexagram_number: Int = 1,
    val name: String = "Ch'ien (Yaratıcı Güç)",
    val judgment: String = "Büyük başarı ve süreklilik. Gökyüzünün enerjisi seninle.",
    val lines: List<Int> = listOf(9, 9, 9, 9, 9, 9)
)

data class IChingResponse(
    val status: String,
    val hexagram: IChingHexagramData?
)

interface IChingApi {
    @POST("api/v1/iching/cast")
    suspend fun castIChing(): IChingResponse
}
