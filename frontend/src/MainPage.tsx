import React, { useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './MainPage.css';
import logo from './assets/logo.png';
import useIntersectionObserver from './useIntersectionObserver';

// --- 컴포넌트들 (기존과 동일) ---
const FirstTitle: React.FC = () => {
  const firstTitleRef = useRef<HTMLDivElement | null>(null);
  const [setTarget, isVisible] = useIntersectionObserver({ threshold: 0.5, rootMargin: '0px 0px -100px 0px' });
  useEffect(() => { if (firstTitleRef.current) setTarget(firstTitleRef.current); }, [setTarget]);
  return (
    <div ref={firstTitleRef} className={`first-title-container ${isVisible ? 'is-visible' : ''}`}>
      <p className="first-title">
        attorney<span className="ask-orange">(변호사)</span> + SK ⇒ <span className="ask-orange">a</span><span className="ask-red">SK</span>: 질문하다
      </p>
      <p className="first-subtitle">SK의 AI 사내 변호사에게 질문할 수 있는 시스템</p>
    </div>
  );
};
const SecondTitle: React.FC = () => {
  const secondTitleRef = useRef<HTMLDivElement | null>(null);
  const [setTarget, isVisible] = useIntersectionObserver({ threshold: 0.8, rootMargin: '0px 0px -150px 0px' });
  useEffect(() => { if (secondTitleRef.current) setTarget(secondTitleRef.current); }, [setTarget]);
  return (
    <h2 ref={secondTitleRef} className={`description-title ${isVisible ? 'is-visible' : ''}`}>
      <span className="ask-orange">a</span><span className="ask-red">SK</span>, 이렇게 다릅니다
    </h2>
  );
};
const featuresData = [
    { title: 'RAG 기반 AI 시스템', description: '사용자의 계약 이슈 분석, 관련 조항 요약 후 근거와 함께 답변하여 신뢰성 확보' },
    { title: 'SK의 차세대 사내 변호사', description: '실무진이 활용 가능한 구체적 대응 전략 및 조언부터, 법령과의 비교를 통한 유불리 분석까지' },
    { title: '통합형 법무 지원 시스템', description: '계약서 초기 검토부터 분쟁 해결까지, 사용자의 업무 전반을 보조하여 업무의 정확성 & 효율성 극대화' },
    { title: '실시간 업데이트 및 지속적인 학습', description: '새로운 법규 및 판례를 반영하여 답변의 정확도를 높이고, 사용자 피드백을 통해 지속적으로 성능 향상' },
];
const FeatureCard: React.FC<{ title: string; description: string; delayClass: string }> = ({ title, description, delayClass }) => {
  const cardRef = useRef<HTMLDivElement | null>(null);
  const [setTarget, isVisible] = useIntersectionObserver({ threshold: 0.3, rootMargin: '0px 0px -100px 0px' });
  useEffect(() => { if (cardRef.current) setTarget(cardRef.current); }, [setTarget]);
  return (
    <div ref={cardRef} className={`feature-card ${delayClass} ${isVisible ? 'is-visible' : ''}`}>
      <h3 className="feature-title">{title}</h3>
      <p className="feature-description">{description}</p>
    </div>
  );
};

const MainPage: React.FC = () => {
  const navigate = useNavigate();
  const pageWrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const pageWrapper = pageWrapperRef.current;
    if (!pageWrapper) return;

    const handleScroll = () => {
      const scrollY = window.scrollY;
      // CSS 변수를 통해 스크롤 Y값을 전달
      pageWrapper.style.setProperty('--scroll-y', `${scrollY}px`);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll(); // 초기 로딩 시 한 번 실행

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  const handleStart = () => {
    navigate('/search');
  };

  return (
    <div ref={pageWrapperRef} className="page-wrapper">
      <div className="main-page-container">
        <img src={logo} alt="aSK Logo" className="main-page-logo" />
        <h1 className="main-page-title">글로벌 계약 정보 검색 시스템</h1>
        <p className="main-page-subtitle">
          복잡하고 어려운 글로벌 계약 문서들, 이제 AI에게 물어보세요.
          정확한 근거와 실무적 조언까지 한 번에 제공해 드립니다.
        </p>
        <button onClick={handleStart} className="start-button">
          시작하기
        </button>
        <div className="scroll-down-arrow">∨</div>
      </div>

      <section className="description-section">
        <FirstTitle />
        <SecondTitle />
        <div className="features-grid">
          {featuresData.map((feature, index) => (
            <FeatureCard
              key={index}
              title={feature.title}
              description={feature.description}
              delayClass={`delay-${index + 1}`}
            />
          ))}
        </div>
      </section>
    </div>
  );
};

export default MainPage;