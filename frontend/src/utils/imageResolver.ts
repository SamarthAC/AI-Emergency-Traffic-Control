import { TrafficCameraData, JunctionCameraDetection } from '../types/dashboard';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const LOCAL_TRAFFIC_CAMERA_FALLBACKS: Record<string, string> = {
  'high1.jpg': '/assets/traffic-cameras/high1.jpg',
  'high2.jpg': '/assets/traffic-cameras/high2.jpg',
  'high3.jpg': '/assets/traffic-cameras/high3.jpg',
  'high4.jpg': '/assets/traffic-cameras/high4.jpg',
  'high5.jpg': '/assets/traffic-cameras/high5.jpg',
  'low1.jpeg': '/assets/traffic-cameras/low1.jpeg',
  'low2.jpg': '/assets/traffic-cameras/low2.jpg',
};

const LOCAL_AMBULANCE_DETECTION_FALLBACKS: Record<string, string> = {
  'test_amb.jpg': '/assets/ambulance-detection/test_amb.jpg',
  'test_amb2.jpeg': '/assets/ambulance-detection/test_amb2.jpeg',
  'test_amb3.jpeg': '/assets/ambulance-detection/test_amb3.jpeg',
  'test_amb4.jpg': '/assets/ambulance-detection/test_amb4.jpg',
  'test_amb5.jpg': '/assets/ambulance-detection/test_amb5.jpg',
  'test_amb6.jpeg': '/assets/ambulance-detection/test_amb6.jpeg',
};

export const AMBULANCE_SAMPLE_GALLERY = [
  { id: 'test_amb2.jpeg', label: 'JCAM J10 Detection Sample (81% Conf)', url: `${API_BASE_URL}/api/images/junction/test_amb2.jpeg`, fallback: '/assets/ambulance-detection/test_amb2.jpeg' },
  { id: 'test_amb.jpg', label: 'Evaluation Sample #1 (Urban Lane)', url: `${API_BASE_URL}/api/images/junction/test_amb.jpg`, fallback: '/assets/ambulance-detection/test_amb.jpg' },
  { id: 'test_amb3.jpeg', label: 'Evaluation Sample #3 (Arterial Approach)', url: `${API_BASE_URL}/api/images/junction/test_amb3.jpeg`, fallback: '/assets/ambulance-detection/test_amb3.jpeg' },
  { id: 'test_amb4.jpg', label: 'Evaluation Sample #4 (Crossroad Angle)', url: `${API_BASE_URL}/api/images/junction/test_amb4.jpg`, fallback: '/assets/ambulance-detection/test_amb4.jpg' },
  { id: 'test_amb5.jpg', label: 'Evaluation Sample #5 (Congested Corridor)', url: `${API_BASE_URL}/api/images/junction/test_amb5.jpg`, fallback: '/assets/ambulance-detection/test_amb5.jpg' },
  { id: 'test_amb6.jpeg', label: 'Evaluation Sample #6 (Junction Closeup)', url: `${API_BASE_URL}/api/images/junction/test_amb6.jpeg`, fallback: '/assets/ambulance-detection/test_amb6.jpeg' },
];

/**
 * Normalizes URL by ensuring API origin if relative
 */
export function normalizeApiUrl(url: string): string {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }
  const cleanPath = url.startsWith('/') ? url : `/${url}`;
  return `${API_BASE_URL}${cleanPath}`;
}

/**
 * Resolves the live traffic camera image URL with cache-busting parameter.
 * Priority:
 * 1. `trafficData.image_url` (with cache-buster)
 * 2. `/api/images/traffic/<cameraId>?v=<version>`
 * 3. Local asset fallback
 */
export function resolveTrafficCameraUrl(
  cameraId: string,
  trafficData?: TrafficCameraData | null,
  defaultImageFallback?: string
): { primaryUrl: string; fallbackUrl: string } {
  const version =
    trafficData?.image_version ??
    trafficData?.simulation_time ??
    (trafficData?.timestamp ? new Date(trafficData.timestamp).getTime() : null);

  const cleanImageName = (trafficData?.image || defaultImageFallback || 'low1.jpeg')
    .split('/')
    .pop()
    ?.split('\\')
    .pop() || 'low1.jpeg';

  const fallbackUrl =
    LOCAL_TRAFFIC_CAMERA_FALLBACKS[cleanImageName] ||
    `/assets/traffic-cameras/${cleanImageName}`;

  let primaryUrl = '';
  if (trafficData?.image_url) {
    primaryUrl = normalizeApiUrl(trafficData.image_url);
  } else if (cameraId) {
    primaryUrl = `${API_BASE_URL}/api/images/traffic/${encodeURIComponent(cameraId)}`;
  } else {
    primaryUrl = fallbackUrl;
  }

  // Append cache busting query param
  if (version !== null && version !== undefined) {
    const separator = primaryUrl.includes('?') ? '&' : '?';
    primaryUrl = `${primaryUrl}${separator}v=${encodeURIComponent(String(version))}`;
  }

  return { primaryUrl, fallbackUrl };
}

/**
 * Backward-compatible helper for traffic camera image string
 */
export function resolveTrafficCameraImage(
  imageName?: string | null,
  cameraId?: string,
  trafficData?: TrafficCameraData | null
): string {
  if (cameraId || trafficData) {
    return resolveTrafficCameraUrl(cameraId || '', trafficData, imageName || undefined).primaryUrl;
  }
  if (!imageName) return '';
  const cleanName = imageName.split('/').pop()?.split('\\').pop() || imageName;
  return LOCAL_TRAFFIC_CAMERA_FALLBACKS[cleanName] || `/assets/traffic-cameras/${cleanName}`;
}

/**
 * Resolves junction camera image URL.
 * Served by backend at `/api/images/junction/{image_name}`
 */
export function resolveJunctionCameraUrl(
  detectionData?: JunctionCameraDetection | null,
  defaultImageFallback: string = 'test_amb2.jpeg'
): { primaryUrl: string; fallbackUrl: string } {
  const meta = detectionData?.metadata;
  const imageName = (meta?.image || defaultImageFallback)
    .split('/')
    .pop()
    ?.split('\\')
    .pop() || defaultImageFallback;

  const fallbackUrl =
    LOCAL_AMBULANCE_DETECTION_FALLBACKS[imageName] ||
    `/assets/ambulance-detection/${imageName}`;

  let primaryUrl = '';
  if (meta?.image_url) {
    primaryUrl = normalizeApiUrl(meta.image_url);
  } else {
    primaryUrl = `${API_BASE_URL}/api/images/junction/${encodeURIComponent(imageName)}`;
  }

  return { primaryUrl, fallbackUrl };
}

/**
 * Backward-compatible helper for ambulance detection image string
 */
export function resolveAmbulanceDetectionImage(
  imageName?: string | null,
  detectionData?: JunctionCameraDetection | null
): string {
  return resolveJunctionCameraUrl(detectionData, imageName || 'test_amb2.jpeg').primaryUrl;
}
