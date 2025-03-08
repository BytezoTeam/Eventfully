/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./eventfully/templates/**/*.html",
    ],
    theme: {
        extend: {},
    },
    plugins: [
        require('@tailwindcss/typography'),
        require("daisyui")
    ],
}
