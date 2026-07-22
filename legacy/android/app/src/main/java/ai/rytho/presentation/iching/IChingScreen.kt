package ai.rytho.presentation.iching

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import ai.rytho.data.remote.IChingHexagramData

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun IChingScreen(
    viewModel: IChingViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("I Ching Kehanet Odası", color = Color(0xFFE7E0ED), fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF0F0C1B))
            )
        },
        containerColor = Color(0xFF0F0C1B)
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(24.dp),
            contentAlignment = Alignment.Center
        ) {
            when (uiState) {
                is IChingUiState.Idle -> {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Text("☯", fontSize = 72.sp, color = Color(0xFFD4AF37))
                        Spacer(modifier = Modifier.height(24.dp))
                        Text(
                            "Zihnindeki Soruyu Odakla",
                            style = MaterialTheme.typography.headlineMedium,
                            color = Color(0xFFE7E0ED),
                            fontWeight = FontWeight.Bold,
                            textAlign = TextAlign.Center
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            "Kadim Çin kehanet yöntemi I Ching için 3 altın parayı salla ve evrenin rehberliğini al.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = Color(0xFF9B8FAE),
                            textAlign = TextAlign.Center
                        )
                        Spacer(modifier = Modifier.height(48.dp))
                        Button(
                            onClick = { viewModel.castCoins() },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(56.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF7C3AED)),
                            shape = RoundedCornerShape(16.dp)
                        ) {
                            Text("Paraları At (Atmosferik Entropi) 🪙", fontSize = 16.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }
                is IChingUiState.Casting -> {
                    CoinCastingAnimation()
                }
                is IChingUiState.Success -> {
                    val hexagram = (uiState as IChingUiState.Success).hexagram
                    HexagramResultView(hexagram = hexagram, onReset = { viewModel.reset() })
                }
                is IChingUiState.Error -> {
                    Text("Hata Oluştu", color = MaterialTheme.colorScheme.error)
                }
            }
        }
    }
}

@Composable
fun CoinCastingAnimation() {
    val infiniteTransition = rememberInfiniteTransition(label = "coin_spin")
    val rotation by infiniteTransition.animateFloat(
        initialValue = 0f, targetValue = 360f,
        animationSpec = infiniteRepeatable(tween(800, easing = LinearEasing)), label = "rot"
    )

    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            repeat(3) {
                Box(
                    modifier = Modifier
                        .size(64.dp)
                        .rotate(rotation)
                        .clip(CircleShape)
                        .background(Brush.radialGradient(listOf(Color(0xFFD4AF37), Color(0xFF85660D))))
                        .border(2.dp, Color(0xFFFFF0B3), CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Text("☯", fontSize = 28.sp, color = Color(0xFF15121B))
                }
            }
        }
        Spacer(modifier = Modifier.height(32.dp))
        Text("Evrensel Entropi Hesaplanıyor...", style = MaterialTheme.typography.bodyLarge, color = Color(0xFF8B5CF6))
    }
}

@Composable
fun HexagramResultView(hexagram: IChingHexagramData, onReset: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("Heksagram #${hexagram.hexagram_number}", style = MaterialTheme.typography.labelLarge, color = Color(0xFFD4AF37))
        Spacer(modifier = Modifier.height(8.dp))
        Text(hexagram.name, style = MaterialTheme.typography.headlineSmall, color = Color(0xFFE7E0ED), fontWeight = FontWeight.Bold)

        Spacer(modifier = Modifier.height(32.dp))

        // Hexagram Lines Representation
        Column(
            verticalArrangement = Arrangement.spacedBy(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            repeat(6) {
                Box(
                    modifier = Modifier
                        .width(160.dp)
                        .height(10.dp)
                        .clip(RoundedCornerShape(4.dp))
                        .background(Color(0xFF8B5CF6))
                )
            }
        }

        Spacer(modifier = Modifier.height(32.dp))

        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF15121B)),
            shape = RoundedCornerShape(16.dp)
        ) {
            Column(modifier = Modifier.padding(20.dp)) {
                Text("Kehanet & Hüküm", style = MaterialTheme.typography.titleMedium, color = Color(0xFFD4AF37), fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(8.dp))
                Text(hexagram.judgment, style = MaterialTheme.typography.bodyMedium, color = Color(0xFFE7E0ED), lineHeight = 22.sp)
            }
        }

        Spacer(modifier = Modifier.weight(1f))

        Button(
            onClick = onReset,
            modifier = Modifier.fillMaxWidth().height(50.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF7C3AED))
        ) {
            Text("Yeni Kehanet Sor")
        }
    }
}
