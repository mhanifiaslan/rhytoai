package ai.rytho.presentation.astrology

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import ai.rytho.data.remote.NatalChartData

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AstrologyScreen(
    viewModel: AstrologyViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Kozmik Harita & Transitler", color = Color(0xFFE7E0ED), fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("🔮", fontSize = 18.sp)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF0F0C1B))
            )
        },
        containerColor = Color(0xFF0F0C1B)
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            when (uiState) {
                is AstrologyUiState.Loading -> {
                    Column(
                        modifier = Modifier.fillMaxSize(),
                        verticalArrangement = Arrangement.Center,
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        CircularProgressIndicator(color = Color(0xFF8B5CF6))
                        Spacer(modifier = Modifier.height(16.dp))
                        Text("Kozmik konumlar ve gezegenler hesaplanıyor...", color = Color(0xFF9B8FAE))
                    }
                }
                is AstrologyUiState.Error -> {
                    Column(
                        modifier = Modifier.fillMaxSize(),
                        verticalArrangement = Arrangement.Center,
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text("Harita Yüklenemedi", color = MaterialTheme.colorScheme.error)
                        Button(onClick = { viewModel.loadNatalChart() }) {
                            Text("Tekrar Denet")
                        }
                    }
                }
                is AstrologyUiState.Success -> {
                    val data = (uiState as AstrologyUiState.Success).chartData
                    NatalChartContent(data = data)
                }
            }
        }
    }
}

@Composable
fun NatalChartContent(data: NatalChartData) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Celestial Big Three Header
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, Brush.linearGradient(listOf(Color(0xFF8B5CF6), Color(0xFFD4AF37))), RoundedCornerShape(20.dp)),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF15121B)),
            shape = RoundedCornerShape(20.dp)
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text("✦ KUTSAL ÜÇLÜ YERLEŞİMİ ✦", style = MaterialTheme.typography.labelMedium, color = Color(0xFFD4AF37), letterSpacing = 2.sp)
                Spacer(modifier = Modifier.height(16.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    SignBadge("Güneş ☀️", data.sun_sign)
                    SignBadge("Ay 🌙", data.moon_sign)
                    SignBadge("Yükselen 🌅", data.ascendant)
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Cosmic Wheel Representation
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF15121B)),
            shape = RoundedCornerShape(20.dp)
        ) {
            Column(modifier = Modifier.padding(20.dp)) {
                Text("Gezegen Konumları & Transit Yorumu", style = MaterialTheme.typography.titleMedium, color = Color(0xFFE7E0ED), fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(12.dp))
                Text(
                    text = data.report.ifEmpty { "Doğum anındaki gezegen açılanmaların spiritüel potansiyelini güçlendiriyor." },
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color(0xFF9B8FAE),
                    lineHeight = 22.sp
                )
            }
        }
    }
}

@Composable
fun SignBadge(title: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Box(
            modifier = Modifier
                .size(60.dp)
                .clip(CircleShape)
                .background(Color(0xFF231F30)),
            contentAlignment = Alignment.Center
        ) {
            Text(title.takeLast(2), fontSize = 24.sp)
        }
        Spacer(modifier = Modifier.height(8.dp))
        Text(title, style = MaterialTheme.typography.labelSmall, color = Color(0xFF7A7090))
        Text(value, style = MaterialTheme.typography.titleSmall, color = Color(0xFFE7E0ED), fontWeight = FontWeight.Bold)
    }
}
