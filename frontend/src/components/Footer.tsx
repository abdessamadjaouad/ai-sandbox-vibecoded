// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/components/Footer.tsx

interface FooterProps {
  onNavigate?: (view: "landing" | "about") => void;
}

export const Footer = ({ onNavigate }: FooterProps) => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="footer__container">
        <div className="footer__brand">
          <div className="footer__logo">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              preserveAspectRatio="xMidYMid meet"
              width="200"
              height="24"
              viewBox="0 0 686 77"
              fill="none"
              className="footer__logo-svg"
            >
              <g id="Logo-Only">
                <path
                  id="Union"
                  d="M101.302 0C122.224 0 139.254 16.9927 139.254 37.8877C139.254 58.7826 122.224 75.7754 101.302 75.7754H0V60.3105H101.302C113.701 60.3105 123.789 50.2499 123.789 37.8877C123.789 25.5254 113.701 15.4639 101.302 15.4639H0V0H101.302ZM469.396 15.4639H368.094C355.695 15.464 345.606 25.5254 345.606 37.8877C345.607 50.2499 355.695 60.3104 368.094 60.3105H469.396V75.7754H368.094C347.162 75.7753 330.143 58.7825 330.143 37.8877C330.143 16.9928 347.171 0.000133362 368.094 0H469.396V15.4639ZM315.333 15.4639C298.777 15.4639 287.151 22.7868 274.843 30.5371C270.849 33.0568 266.802 35.5953 262.581 37.8604C266.802 40.1253 270.85 42.663 274.843 45.1826C287.151 52.933 298.777 60.2559 315.333 60.2559V75.7207C294.31 75.7207 279.592 66.4513 266.602 58.2734C255.804 51.4782 246.479 45.6016 235.054 45.6016C223.628 45.6016 214.304 51.4692 203.506 58.2734C190.516 66.4513 175.797 75.7207 154.774 75.7207V60.2559C171.331 60.2559 182.957 52.933 195.265 45.1826C199.258 42.663 203.306 40.1253 207.526 37.8604C203.306 35.5953 199.258 33.0568 195.265 30.5371C182.957 22.7868 171.331 15.4639 154.774 15.4639V0C175.797 0 190.516 9.26912 203.506 17.4561C214.304 24.2512 223.628 30.1279 235.054 30.1279V30.1191C246.479 30.1191 255.804 24.2516 266.602 17.4473C279.592 9.26941 294.31 5.90241e-06 315.333 0V15.4639Z"
                  fill="url(#paint0_radial_footer)"
                />
                <defs>
                  <radialGradient
                    id="paint0_radial_footer"
                    cx="0"
                    cy="0"
                    r="1"
                    gradientTransform="matrix(256.303 -72.3188 31.2673 110.811 236.29 37.7513)"
                    gradientUnits="userSpaceOnUse"
                  >
                    <stop stopColor="#FFB87E" />
                    <stop offset="0.163458" stopColor="#FFA962" />
                    <stop offset="0.337937" stopColor="#FEA15F" />
                    <stop offset="0.557693" stopColor="#FF7E51" />
                    <stop offset="0.839777" stopColor="#B88A99" />
                    <stop offset="1" stopColor="#6399F0" />
                  </radialGradient>
                </defs>
              </g>
            </svg>
          </div>
          <p className="footer__tagline">IMPOSSIBLE. DELIVERED.</p>
        </div>

        <div className="footer__column">
          <h4 className="footer__nav-title">Company</h4>
          <ul className="footer__nav-list">
            <li><button onClick={() => onNavigate?.("about")} className="footer__link">About Us</button></li>
            <li><a href="https://dxc.com/us/en/about-us/leadership" target="_blank" rel="noopener noreferrer" className="footer__link">Leadership</a></li>
            <li><a href="https://dxc.com/us/en/about-us/corporate-responsibility" target="_blank" rel="noopener noreferrer" className="footer__link">Corporate Responsibility</a></li>
          </ul>
        </div>

        <div className="footer__column">
          <h4 className="footer__nav-title">Resources</h4>
          <ul className="footer__nav-list">
            <li><a href="#" className="footer__link">Documentation</a></li>
            <li><a href="#" className="footer__link">API Reference</a></li>
            <li><a href="#" className="footer__link">Support</a></li>
          </ul>
        </div>

        <div className="footer__column">
          <h4 className="footer__nav-title">Legal</h4>
          <ul className="footer__nav-list">
            <li><a href="#" className="footer__link">Privacy Policy</a></li>
            <li><a href="#" className="footer__link">Terms of Service</a></li>
            <li><a href="#" className="footer__link">Cookie Policy</a></li>
          </ul>
        </div>

        <div className="footer__column">
          <h4 className="footer__nav-title">Contact</h4>
          <ul className="footer__nav-list">
            <li><a href="#" className="footer__link">Contact Us</a></li>
            <li><a href="#" className="footer__link">Careers</a></li>
            <li><a href="https://dxc.com" target="_blank" rel="noopener noreferrer" className="footer__link">DXC.com</a></li>
          </ul>
        </div>

        <div className="footer__bottom">
          <p className="footer__copyright">
            &copy; {currentYear} DXC Technology Company. All rights reserved.
          </p>
          <p className="footer__project">
            AI Sandbox is a project by DXC Technology &amp; ENSAM Casablanca
          </p>
        </div>
      </div>
    </footer>
  );
};
