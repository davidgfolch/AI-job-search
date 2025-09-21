/** @type {import('tailwindcss').Config} */
export const darkMode = ['class'];
export const content = [
	'./src/pages/**/*.{js,ts,jsx,tsx,mdx}',
	'./src/components/**/*.{js,ts,jsx,tsx,mdx}',
	'./src/app/**/*.{js,ts,jsx,tsx,mdx}',
];
export const theme = {
	extend: {
		colors: {
			primary: {
				'50': '#eff6ff',
				'100': '#dbeafe',
				'200': '#bfdbfe',
				'300': '#93c5fd',
				'400': '#60a5fa',
				'500': '#3b82f6',
				'600': '#2563eb',
				'700': '#1d4ed8',
				'800': '#1e40af',
				'900': '#1e3a8a',
				DEFAULT: 'hsl(var(--primary))',
				foreground: 'hsl(var(--primary-foreground))'
			},
			success: {
				'50': '#f0fdf4',
				'500': '#22c55e',
				'600': '#16a34a'
			},
			warning: {
				'50': '#fffbeb',
				'500': '#f59e0b',
				'600': '#d97706'
			},
			error: {
				'50': '#fef2f2',
				'500': '#ef4444',
				'600': '#dc2626'
			},
			gray: {
				'50': '#f9fafb',
				'100': '#f3f4f6',
				'200': '#e5e7eb',
				'300': '#d1d5db',
				'400': '#9ca3af',
				'500': '#6b7280',
				'600': '#4b5563',
				'700': '#374151',
				'800': '#1f2937',
				'900': '#111827'
			},
			background: 'hsl(var(--background))',
			foreground: 'hsl(var(--foreground))',
			card: {
				DEFAULT: 'hsl(var(--card))',
				foreground: 'hsl(var(--card-foreground))'
			},
			popover: {
				DEFAULT: 'hsl(var(--popover))',
				foreground: 'hsl(var(--popover-foreground))'
			},
			secondary: {
				DEFAULT: 'hsl(var(--secondary))',
				foreground: 'hsl(var(--secondary-foreground))'
			},
			muted: {
				DEFAULT: 'hsl(var(--muted))',
				foreground: 'hsl(var(--muted-foreground))'
			},
			accent: {
				DEFAULT: 'hsl(var(--accent))',
				foreground: 'hsl(var(--accent-foreground))'
			},
			destructive: {
				DEFAULT: 'hsl(var(--destructive))',
				foreground: 'hsl(var(--destructive-foreground))'
			},
			border: 'hsl(var(--border))',
			input: 'hsl(var(--input))',
			ring: 'hsl(var(--ring))',
			chart: {
				'1': 'hsl(var(--chart-1))',
				'2': 'hsl(var(--chart-2))',
				'3': 'hsl(var(--chart-3))',
				'4': 'hsl(var(--chart-4))',
				'5': 'hsl(var(--chart-5))'
			}
		},
		fontFamily: {
			sans: [
				'Inter',
				'system-ui',
				'sans-serif'
			]
		},
		spacing: {
			'18': '4.5rem',
			'88': '22rem'
		},
		animation: {
			'fade-in': 'fadeIn 0.5s ease-in-out',
			'slide-in': 'slideIn 0.3s ease-out',
			'pulse-slow': 'pulse 3s infinite'
		},
		keyframes: {
			fadeIn: {
				'0%': {
					opacity: '0'
				},
				'100%': {
					opacity: '1'
				}
			},
			slideIn: {
				'0%': {
					transform: 'translateX(-100%)'
				},
				'100%': {
					transform: 'translateX(0)'
				}
			}
		},
		borderRadius: {
			lg: 'var(--radius)',
			md: 'calc(var(--radius) - 2px)',
			sm: 'calc(var(--radius) - 4px)'
		}
	}
};
export const plugins = {
	tailwindcss: {},
	autoprefixer: {},
}