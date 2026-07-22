package ai.rytho.presentation.social

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import ai.rytho.domain.model.SocialPost

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SocialScreen(
    viewModel: SocialViewModel = hiltViewModel()
) {
    val posts by viewModel.posts.collectAsState()
    var postText by remember { mutableStateOf("") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            "Kozmik Ağ",
                            style = MaterialTheme.typography.titleLarge,
                            color = Color(0xFFE7E0ED),
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(8.dp))
                                .background(Color(0xFF8B5CF6).copy(alpha = 0.2f))
                                .padding(horizontal = 8.dp, vertical = 2.dp)
                        ) {
                            Text("Sosyal Akış", color = Color(0xFF8B5CF6), style = MaterialTheme.typography.labelSmall)
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF0F0C1B))
            )
        },
        containerColor = Color(0xFF0F0C1B)
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // Post creation input
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF15121B)),
                shape = RoundedCornerShape(16.dp)
            ) {
                Row(
                    modifier = Modifier.padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    OutlinedTextField(
                        value = postText,
                        onValueChange = { postText = it },
                        placeholder = { Text("Kozmik enerjini veya burç yorumunu paylaş...", color = Color(0xFF7A7090)) },
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(12.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = Color(0xFF8B5CF6),
                            unfocusedBorderColor = Color(0xFF2E273F),
                            focusedTextColor = Color(0xFFE7E0ED),
                            unfocusedTextColor = Color(0xFFE7E0ED)
                        )
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    IconButton(
                        onClick = {
                            if (postText.isNotBlank()) {
                                viewModel.createPost(postText)
                                postText = ""
                            }
                        },
                        enabled = postText.isNotBlank(),
                        modifier = Modifier
                            .size(48.dp)
                            .clip(CircleShape)
                            .background(if (postText.isNotBlank()) Color(0xFF7C3AED) else Color(0xFF2E273F))
                    ) {
                        Icon(Icons.AutoMirrored.Filled.Send, contentDescription = "Paylaş", tint = Color.White)
                    }
                }
            }

            // Social Feed Posts
            if (posts.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .weight(1f),
                    contentAlignment = Alignment.Center
                ) {
                    Text("Henüz paylaşım yapılmadı. İlk kozmik mesajı sen gönder! ✨", color = Color(0xFF7A7090))
                }
            } else {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .weight(1f)
                        .padding(horizontal = 16.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                    contentPadding = PaddingValues(bottom = 16.dp)
                ) {
                    items(posts, key = { it.id }) { post ->
                        SocialPostCard(post = post)
                    }
                }
            }
        }
    }
}

@Composable
fun SocialPostCard(post: SocialPost) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, Color(0xFF8B5CF6).copy(alpha = 0.15f), RoundedCornerShape(16.dp)),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF15121B)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .clip(CircleShape)
                        .background(
                            Brush.linearGradient(
                                colors = listOf(Color(0xFF8B5CF6), Color(0xFFD4AF37))
                            )
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        post.authorName.take(1).uppercase().ifEmpty { "✦" },
                        color = Color.White,
                        fontWeight = FontWeight.Bold
                    )
                }
                Spacer(modifier = Modifier.width(12.dp))
                Column {
                    Text(
                        post.authorName.ifEmpty { "Kozmik Gezgin" },
                        style = MaterialTheme.typography.titleMedium,
                        color = Color(0xFFE7E0ED),
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        post.authorZodiac,
                        style = MaterialTheme.typography.labelSmall,
                        color = Color(0xFFD4AF37)
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = post.content,
                style = MaterialTheme.typography.bodyMedium,
                color = Color(0xFFE7E0ED),
                lineHeight = 20.sp
            )

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                horizontalArrangement = Arrangement.spacedBy(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = {}) {
                    Icon(Icons.Default.Favorite, contentDescription = "Beğen", tint = Color(0xFFE5484D))
                }
                Text("${post.likesCount}", color = Color(0xFF9B8FAE), style = MaterialTheme.typography.bodySmall)

                Spacer(modifier = Modifier.weight(1f))

                IconButton(onClick = {}) {
                    Icon(Icons.Default.Share, contentDescription = "Paylaş", tint = Color(0xFF7A7090))
                }
            }
        }
    }
}
