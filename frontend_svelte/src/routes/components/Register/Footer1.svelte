<script lang="ts">
    interface Props {
        logo?: string;
    }

    let { logo = "/assets/img/logo.png" }: Props = $props();
</script>

<footer class="footer">
    <!-- Main Footer Content -->
    <div class="footer-container">
        <!-- Brand Section -->
        <div class="footer-brand">
            <img src={logo || "/placeholder.svg"} alt="AtoZFlix Logo" class="logo" />
            <p class="brand-description">AtoZFlix is a personalized movie recommendation platform that curates the perfect cinematic experience tailored just for you. Discover, rate, and enjoy movies from around the world.</p>
        </div>
        
        <!-- Navigation Links -->
        <div class="footer-sections">
            <!-- Browse Section -->
            <div class="footer-section">
                <h3 class="section-title">Browse</h3>
                <ul class="footer-links">
                    <li><a href="/genres" class="footer-link">Genres</a></li>
                    <li><a href="/actors" class="footer-link">Actors</a></li>
                    <li><a href="/countries" class="footer-link">Countries</a></li>
                    <li><a href="/trending" class="footer-link">Trending</a></li>
                </ul>
            </div>

            <!-- My Lists Section -->
            <div class="footer-section">
                <h3 class="section-title">My Lists</h3>
                <ul class="footer-links">
                    <li><a href="/favorites" class="footer-link">Favorites</a></li>
                    <li><a href="/watchlater" class="footer-link">Watch Later</a></li>
                    <li><a href="/personalized" class="footer-link">For You</a></li>
                    <li><a href="/ratings" class="footer-link">My Ratings</a></li>
                </ul>
            </div>

            <!-- Support & Connect Section -->
            <div class="footer-section">
                <h3 class="section-title">Support & Connect</h3>
                <ul class="footer-links">
                    <li><a href="/feedback" class="footer-link">Feedback</a></li>
                    <li><a href="/privacy" class="footer-link">Privacy Policy</a></li>
                    <li><a href="/terms" class="footer-link">Terms of Service</a></li>
                    <li><a href="/about" class="footer-link">About Me</a></li>
                </ul>
            </div>
            
            <!-- Creator Section -->
            <div class="footer-section">
                <h3 class="section-title">Creator</h3>
                <div class="creator-card">
                    <div class="creator-info">
                        <img src="/assets/img/ZainB.png" alt="Zain Baig" class="creator-pic" />
                        <div class="creator-details">
                            <h4 class="creator-name">Zain Baig</h4>
                            <p class="creator-role">Full Stack Developer</p>
                            <div class="creator-links">
                                <a href="https://www.linkedin.com/in/zain-baig-04790b260/" target="_blank" class="social-link">
                                    LinkedIn
                                </a>
                                <a href="https://github.com/zainbaig" target="_blank" class="social-link">
                                    GitHub
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer Bottom -->
    <div class="footer-bottom">
        <div class="footer-bottom-content">
            <!-- Language Selector -->
            <div class="language-selector">
                <select name="language" id="language" class="language-dropdown">
                    <option value="en">🇺🇸 English</option>
                    <option value="ur">🇵🇰 اردو</option>
                    <option value="es">🇪🇸 Español</option>
                    <option value="fr">🇫🇷 Français</option>
                    <option value="de">🇩🇪 Deutsch</option>
                    <option value="ja">🇯🇵 日本語</option>
                    <option value="ko">🇰🇷 한국어</option>
                </select>
            </div>

            <!-- Copyright -->
            <div class="copyright">
                <p>&copy; 2024 AtoZFlix Pakistan. All rights reserved.</p>
                <p class="tagline">Crafted with ❤️ for movie enthusiasts worldwide</p>
            </div>

            <!-- Region -->
            <div class="region">
                <span class="region-text">🌍 Pakistan</span>
            </div>
        </div>
    </div>
</footer>
    
<style>
.footer {
    background: #111;
    color: #ffffff;
    padding: 40px 0 20px;
    font-family: 'Netflix Sans', 'Helvetica Neue', 'Segoe UI', 'Roboto', 'Ubuntu', sans-serif;
    border-top: 1px solid #333;
}

.footer-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 30px;
}

/* Brand Section */
.footer-brand {
    text-align: center;
    margin-bottom: 40px;
}

.logo {
    width: 140px;
    height: auto;
    margin-bottom: 15px;
}

.brand-description {
    font-size: 0.95rem;
    color: rgba(255, 255, 255, 0.7);
    max-width: 600px;
    margin: 0 auto;
    line-height: 1.6;
}

/* Navigation Sections */
.footer-sections {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 30px;
    margin-bottom: 40px;
}

.footer-section {
    padding: 0;
}

.section-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #098577;
    margin-bottom: 20px;
    position: relative;
}

.section-title::after {
    content: '';
    position: absolute;
    bottom: -5px;
    left: 0;
    width: 30px;
    height: 2px;
    background: #098577;
}

.footer-links {
    list-style: none;
    padding: 0;
    margin: 0;
}

.footer-links li {
    margin-bottom: 12px;
}

.footer-link {
    color: rgba(255, 255, 255, 0.8);
    text-decoration: none;
    font-size: 0.95rem;
    transition: all 0.3s ease;
    display: inline-block;
}

.footer-link:hover {
    color: #098577;
    transform: translateX(3px);
}

/* Creator Section */
.creator-card {
    margin-top: 0;
}

.creator-info {
    display: flex;
    align-items: center;
    gap: 15px;
}

.creator-pic {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid #333;
}

.creator-details {
    flex: 1;
}

.creator-name {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 4px;
    color: #ffffff;
}

.creator-role {
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 8px;
    font-size: 0.85rem;
}

.creator-links {
    display: flex;
    gap: 12px;
}

.social-link {
    color: rgba(255, 255, 255, 0.8);
    text-decoration: none;
    font-size: 0.85rem;
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid #333;
    transition: all 0.3s ease;
}

.social-link:hover {
    color: #098577;
    border-color: #098577;
}

/* Footer Bottom */
.footer-bottom {
    border-top: 1px solid #333;
    padding-top: 25px;
}

.footer-bottom-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 20px;
}

.language-dropdown {
    background: #1a1a1a;
    color: white;
    border: 1px solid #333;
    padding: 10px 15px;
    border-radius: 4px;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.3s ease;
}

.language-dropdown:hover {
    border-color: #098577;
}

.copyright {
    text-align: center;
    flex: 1;
}

.copyright p {
    margin: 5px 0;
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.9rem;
}

.tagline {
    font-style: italic;
    color: rgba(255, 255, 255, 0.5) !important;
}

.region-text {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.9rem;
}

/* Responsive Design */
@media (max-width: 768px) {
    .footer-container {
        padding: 0 20px;
    }
    
    .footer-sections {
        grid-template-columns: 1fr;
        gap: 25px;
    }
    
    .creator-info {
        flex-direction: column;
        text-align: center;
    }
    
    .footer-bottom-content {
        flex-direction: column;
        text-align: center;
        gap: 15px;
        padding: 0 20px;
    }
    
    .logo {
        width: 100px;
    }
    
    .brand-description {
        font-size: 0.9rem;
    }
}
</style>
