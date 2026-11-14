// GLSL for the globe and its atmosphere. Textures are sampled in linear space
// (three.js converts sRGB textures) and the result is converted back with
// <colorspace_fragment>, so colours match the source images.

export const globeVertex = /* glsl */ `
  varying vec2 vUv;
  varying vec3 vWorldNormal;
  varying vec3 vWorldPos;
  void main() {
    vUv = uv;
    vec4 wp = modelMatrix * vec4(position, 1.0);
    vWorldPos = wp.xyz;
    vWorldNormal = normalize(mat3(modelMatrix) * normal);
    gl_Position = projectionMatrix * viewMatrix * wp;
  }
`

export const globeFragment = /* glsl */ `
  uniform sampler2D dayMap;
  uniform sampler2D nightMap;
  uniform sampler2D waterMap;
  uniform vec3 sunDir;
  uniform float ready;      // 0 until textures arrive, then fades to 1
  uniform float dataTint;   // 0 = natural colours, 1 = analytical blue tint
  varying vec2 vUv;
  varying vec3 vWorldNormal;
  varying vec3 vWorldPos;

  void main() {
    vec3 N = normalize(vWorldNormal);
    vec3 V = normalize(cameraPosition - vWorldPos);
    float ndl = dot(N, sunDir);
    float dayMix = smoothstep(-0.10, 0.28, ndl);

    vec3 day = texture2D(dayMap, vUv).rgb;
    vec3 night = texture2D(nightMap, vUv).rgb;
    float water = texture2D(waterMap, vUv).r;

    vec3 dayCol = day * (0.18 + 1.05 * max(ndl, 0.0));
    vec3 H = normalize(sunDir + V);
    dayCol += vec3(0.85, 0.92, 1.0) * pow(max(dot(N, H), 0.0), 140.0) * water * 0.2;

    // City lights: keep the warm, bright pixels, damp the dark-blue base of the night image.
    float lights = smoothstep(0.10, 0.55, max(night.r, night.g));
    vec3 nightCol = night * 0.35 + vec3(1.0, 0.78, 0.45) * lights * 1.35;

    vec3 col = mix(nightCol, dayCol, dayMix);

    float fres = pow(1.0 - max(dot(N, V), 0.0), 2.6);
    col += vec3(0.22, 0.52, 1.0) * fres * (0.25 + 0.55 * dayMix);

    float l = dot(col, vec3(0.2126, 0.7152, 0.0722));
    col = mix(col, l * vec3(0.45, 0.78, 1.2), dataTint * 0.5);

    vec3 placeholder = vec3(0.015, 0.035, 0.08) + vec3(0.1, 0.3, 0.7) * fres;
    gl_FragColor = vec4(mix(placeholder, col, ready), 1.0);
    #include <colorspace_fragment>
  }
`

export const atmosphereVertex = /* glsl */ `
  varying vec3 vNormalView;
  varying vec3 vWorldNormal;
  void main() {
    vNormalView = normalize(normalMatrix * normal);
    vWorldNormal = normalize(mat3(modelMatrix) * normal);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`

export const atmosphereFragment = /* glsl */ `
  uniform vec3 sunDir;
  uniform vec3 glow;
  uniform float strength;
  varying vec3 vNormalView;
  varying vec3 vWorldNormal;
  void main() {
    float rim = pow(clamp(0.78 - dot(vNormalView, vec3(0.0, 0.0, 1.0)), 0.0, 1.0), 3.2);
    float lit = 0.35 + 0.65 * smoothstep(-0.35, 0.6, dot(normalize(vWorldNormal), sunDir));
    gl_FragColor = vec4(glow * rim * lit * strength, rim * strength);
  }
`
