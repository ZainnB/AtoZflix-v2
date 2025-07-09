<footer class="footer">
    <!-- Main Footer Content -->
    <div class="footer-container">
        <!-- Brand Section -->
        <div class="footer-brand">
            <h2 class="brand-title">AtoZFlix</h2>
            <p class="brand-tagline">Your Gateway to Cinematic Excellence</p>
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
                    <li><a href="/new-releases" class="footer-link">New Releases</a></li>
                </ul>
            </div>

            <!-- My Lists Section -->
            <div class="footer-section">
                <h3 class="section-title">My Lists</h3>
                <ul class="footer-links">
                    <li><a href="/favorites" class="footer-link">Favorites</a></li>
                    <li><a href="/watchlater" class="footer-link">Watch Later</a></li>
                    <li><a href="/personalized" class="footer-link">For You</a></li>
                    <li><a href="/history" class="footer-link">Watch History</a></li>
                    <li><a href="/ratings" class="footer-link">My Ratings</a></li>
                </ul>
            </div>

            <!-- Support Section -->
            <div class="footer-section">
                <h3 class="section-title">Support</h3>
                <ul class="footer-links">
                    <li><a href="/help" class="footer-link">Help Center</a></li>
                    <li><a href="/contact" class="footer-link">Contact Us</a></li>
                    <li><a href="/feedback" class="footer-link">Feedback</a></li>
                    <li><a href="/privacy" class="footer-link">Privacy Policy</a></li>
                    <li><a href="/terms" class="footer-link">Terms of Service</a></li>
                </ul>
            </div>

            <!-- Connect Section -->
            <div class="footer-section">
                <h3 class="section-title">Connect</h3>
                <ul class="footer-links">
                    <li><a href="/about" class="footer-link">About Us</a></li>
                    <li><a href="/blog" class="footer-link">Blog</a></li>
                    <li><a href="/careers" class="footer-link">Careers</a></li>
                    <li><a href="/press" class="footer-link">Press</a></li>
                    <li><a href="/api" class="footer-link">Developer API</a></li>
                </ul>
            </div>
        </div>

        <!-- Creator Section -->
        <div class="creator-section">
            <div class="creator-card">
                <div class="creator-avatar">
                    <img src="/assets/img/ZainB.png" alt="Zain Baig" class="creator-pic" />
                    <div class="creator-glow"></div>
                </div>
                <div class="creator-info">
                    <h4 class="creator-name">Zain Baig</h4>
                    <p class="creator-role">Full Stack Developer</p>
                    <div class="creator-links">
                        <a href="https://www.linkedin.com/in/zain-baig-04790b260/" target="_blank" class="social-link linkedin">
                            <span class="social-icon">💼</span>
                            LinkedIn
                        </a>
                        <a href="https://github.com/zainbaig" target="_blank" class="social-link github">
                            <span class="social-icon">🐱</span>
                            GitHub
                        </a>
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
                <select name="language" id="language" class="language-dropdown" oninput={(event) => event.preventDefault()}>
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

    <!-- Cinematic Background Elements -->
    <div class="cinema-bg">
        <div class="film-strip"></div>
        <div class="spotlight spotlight-1"></div>
        <div class="spotlight spotlight-2"></div>
    </div>
</footer>

<style>
.footer {
    position: relative;
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0f0f0f 100%);
    color: #ffffff;
    padding: 60px 0 20px;
    font-family: 'Netflix Sans', 'Helvetica Neue', 'Segoe UI', 'Roboto', 'Ubuntu', sans-serif;
    overflow: hidden;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 40px;
    position: relative;
    z-index: 2;
}

/* Brand Section */
.footer-brand {
    text-align: center;
    margin-bottom: 50px;
}

.brand-title {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(45deg, #00d4aa, #098577, #00d4aa);
    background-size: 200% 200%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradientShift 3s ease-in-out infinite;
    margin-bottom: 10px;
    text-shadow: 0 0 30px rgba(0, 212, 170, 0.3);
}

.brand-tagline {
    font-size: 1.1rem;
    color: rgba(255, 255, 255, 0.7);
    font-style: italic;
}

@keyframes gradientShift {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}

/* Navigation Sections */
.footer-sections {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 40px;
    margin-bottom: 50px;
}

.footer-section {
    background: rgba(255, 255, 255, 0.02);
    padding: 25px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

.footer-section:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(0, 212, 170, 0.3);
    transform: translateY(-2px);
}

.section-title {
    font-size: 1.3rem;
    font-weight: 600;
    color: #00d4aa;
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
    background: linear-gradient(90deg, #00d4aa, transparent);
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
    position: relative;
}

.footer-link:hover {
    color: #00d4aa;
    transform: translateX(5px);
}

.footer-link::before {
    content: '▶';
    position: absolute;
    left: -15px;
    opacity: 0;
    transition: opacity 0.3s ease;
    color: #00d4aa;
    font-size: 0.8rem;
}

.footer-link:hover::before {
    opacity: 1;
}

/* Creator Section */
.creator-section {
    display: flex;
    justify-content: center;
    margin-bottom: 40px;
}

.creator-card {
    background: linear-gradient(135deg, rgba(0, 212, 170, 0.1), rgba(9, 133, 119, 0.1));
    padding: 30px;
    border-radius: 20px;
    border: 1px solid rgba(0, 212, 170, 0.2);
    backdrop-filter: blur(15px);
    display: flex;
    align-items: center;
    gap: 25px;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.creator-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 40px rgba(0, 212, 170, 0.2);
}

.creator-avatar {
    position: relative;
}

.creator-pic {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid #00d4aa;
    position: relative;
    z-index: 2;
}

.creator-glow {
    position: absolute;
    top: -10px;
    left: -10px;
    right: -10px;
    bottom: -10px;
    background: radial-gradient(circle, rgba(0, 212, 170, 0.3), transparent);
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.7; }
    50% { transform: scale(1.1); opacity: 0.3; }
}

.creator-name {
    font-size: 1.4rem;
    font-weight: 600;
    margin-bottom: 5px;
    color: #ffffff;
}

.creator-role {
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 15px;
    font-size: 0.9rem;
}

.creator-links {
    display: flex;
    gap: 15px;
}

.social-link {
    display: flex;
    align-items: center;
    gap: 8px;
    color: rgba(255, 255, 255, 0.8);
    text-decoration: none;
    font-size: 0.9rem;
    padding: 8px 12px;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
}

.social-link:hover {
    background: rgba(0, 212, 170, 0.2);
    color: #00d4aa;
    transform: translateY(-2px);
}

.social-icon {
    font-size: 1.1rem;
}

/* Footer Bottom */
.footer-bottom {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 30px;
    position: relative;
    z-index: 2;
}

.footer-bottom-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 20px;
}

.language-dropdown {
    background: rgba(255, 255, 255, 0.1);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.2);
    padding: 10px 15px;
    border-radius: 8px;
    font-size: 0.9rem;
    cursor: pointer;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

.language-dropdown:hover {
    background: rgba(255, 255, 255, 0.15);
    border-color: #00d4aa;
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

/* Cinematic Background Elements */
.cinema-bg {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
    z-index: 1;
}

.film-strip {
    position: absolute;
    top: 0;
    left: -100px;
    width: 200px;
    height: 100%;
    background: repeating-linear-gradient(
        90deg,
        transparent,
        transparent 10px,
        rgba(255, 255, 255, 0.02) 10px,
        rgba(255, 255, 255, 0.02) 20px
    );
    transform: rotate(-15deg);
    opacity: 0.3;
}

.spotlight {
    position: absolute;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(0, 212, 170, 0.1), transparent);
    animation: spotlightMove 8s ease-in-out infinite;
}

.spotlight-1 {
    width: 300px;
    height: 300px;
    top: -150px;
    right: -150px;
    animation-delay: 0s;
}

.spotlight-2 {
    width: 200px;
    height: 200px;
    bottom: -100px;
    left: -100px;
    animation-delay: 4s;
}

@keyframes spotlightMove {
    0%, 100% { transform: translate(0, 0) scale(1); }
    50% { transform: translate(20px, -20px) scale(1.1); }
}

/* Responsive Design */
@media (max-width: 768px) {
    .footer-container {
        padding: 0 20px;
    }
    
    .footer-sections {
        grid-template-columns: 1fr;
        gap: 20px;
    }
    
    .creator-card {
        flex-direction: column;
        text-align: center;
    }
    
    .footer-bottom-content {
        flex-direction: column;
        text-align: center;
        gap: 15px;
    }
    
    .brand-title {
        font-size: 2rem;
    }
}
</style>
