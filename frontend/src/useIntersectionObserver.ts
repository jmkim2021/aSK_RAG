import { useEffect, useRef, useState } from 'react';

// Intersection Observer를 설정하기 위한 옵션 인터페이스
interface ObserverOptions {
  root?: Element | null;
  rootMargin?: string;
  threshold?: number | number[];
}

// Hook이 반환할 값의 타입 (관찰할 대상을 설정하는 함수)
type SetTarget = (node: Element | null) => void;

// 커스텀 Hook: 요소가 화면에 보이는지 감지
function useIntersectionObserver(options: ObserverOptions): [SetTarget, boolean] {
  const { root = null, rootMargin = '0px', threshold = 0 } = options;
  const [target, setTarget] = useState<Element | null>(null);
  const [isIntersecting, setIsIntersecting] = useState(false);
  const observer = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    if (!target) {
      return;
    }

    // IntersectionObserver 인스턴스 생성
    observer.current = new IntersectionObserver(
      ([entry]) => {
        // isIntersecting 상태 업데이트
        setIsIntersecting(entry.isIntersecting);
      },
      { root, rootMargin, threshold }
    );

    // 관찰 시작
    observer.current.observe(target);

    // 컴포넌트가 언마운트될 때 관찰 중지
    return () => {
      observer.current?.disconnect();
    };
  }, [target, root, rootMargin, threshold]);

  return [setTarget, isIntersecting];
}

export default useIntersectionObserver;