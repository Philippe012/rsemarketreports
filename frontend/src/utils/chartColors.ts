export const CHART_COLORS = {
  light: {
    previous: '#d3d4d1',
    today: '#14161a',
    grid: '#e2e2df',
    axis: '#8a8d91',
    text: '#5c5f63',
    surface: '#ffffff',
    border: '#e2e2df',
  },
  dark: {
    previous: '#3c4044',
    today: '#f4f4f3',
    grid: '#2c2f32',
    axis: '#75797d',
    text: '#a4a8ac',
    surface: '#1b1d1f',
    border: '#2c2f32',
  },
} as const;

export type ChartPalette = (typeof CHART_COLORS)['light'];
