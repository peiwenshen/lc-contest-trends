import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, MultipleLocator

# Each theme is a full set of chart roles, stepped for its own surface, so the
# light and dark PNGs are two deliberate renders rather than an inverted image.
THEMES = {
    'light': {
        'surface': '#fcfcfb',
        'ink': '#0b0b0b',
        'secondary': '#52514e',
        'muted': '#898781',
        'grid': '#e1e0d9',
        'axis': '#c3c2b7',
        'series': '#2a78d6',   # categorical slot 1 - blue
        'trend': '#eb6834',    # categorical slot 2 - orange
        'range_alpha': 0.30,
    },
    'dark': {
        'surface': '#1a1a19',
        'ink': '#ffffff',
        'secondary': '#c3c2b7',
        'muted': '#898781',
        'grid': '#2c2c2a',
        'axis': '#383835',
        'series': '#3987e5',
        'trend': '#d95926',
        'range_alpha': 0.38,
    },
}

SOURCE_NOTE = 'Data: github.com/zerotrac/leetcode_problem_rating'

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica Neue', 'Helvetica', 'Arial', 'DejaVu Sans'],
    'savefig.dpi': 200,
})


def get_contest_ratings(data, top_two_only=False):
    # Initialize a DataFrame to hold contest data
    candlestick_data = []

    # Group by Contest Slug for contests (weekly or biweekly)
    grouped = data.groupby('Contest Slug')

    # Iterate over each group (each contest)
    for contest, group in grouped:
        if len(group) >= 2:  # Ensure there are at least 2 problems
            if top_two_only:
                # Sort the ratings and select the top 2 highest
                ratings = group['Rating'].sort_values(ascending=False).head(2)
            else:
                # Use all ratings
                ratings = group['Rating']

            min_val = ratings.min()
            max_val = ratings.max()
            mean_val = ratings.mean()  # Calculate the mean here
            candlestick_data.append([contest, min_val, max_val, mean_val])

    # Convert to DataFrame
    candlestick_df = pd.DataFrame(candlestick_data, columns=['Contest', 'Min', 'Max', 'Mean'])

    # Strip the contest prefix to leave only the contest number
    # and filter out any non-numeric entries
    candlestick_df['Contest'] = candlestick_df['Contest'].str.replace(r'(weekly|biweekly)-contest-', '', regex=True)

    # Filter out rows where 'Contest' is not numeric
    candlestick_df = candlestick_df[candlestick_df['Contest'].str.isnumeric()]

    # Convert 'Contest' to integer
    candlestick_df['Contest'] = candlestick_df['Contest'].astype(int)

    # Sort by the contest number (which is now an integer)
    candlestick_df = candlestick_df.sort_values('Contest')

    return candlestick_df


def _draw(ax, candlestick_df, theme, trend):
    x = candlestick_df['Contest']
    p, slope = trend

    # Recessive horizontal hairline grid, behind the marks
    ax.set_axisbelow(True)
    ax.grid(axis='y', color=theme['grid'], linewidth=0.8, zorder=0)

    # Min-max range as a thin, low-contrast band of verticals: context, not the
    # subject, so it stays in the series hue at low alpha instead of black. Dense
    # series get thinner bars so they read as a band rather than a solid wall.
    dense = len(candlestick_df) > 200
    ax.vlines(x, candlestick_df['Min'], candlestick_df['Max'], color=theme['series'],
              alpha=theme['range_alpha'], linewidth=0.9 if dense else 1.6, zorder=1)

    # Mean marker, with a surface-colored ring so overlapping dots stay countable
    ax.scatter(x, candlestick_df['Mean'], s=17, color=theme['series'],
               edgecolors=theme['surface'], linewidths=0.5, zorder=3)

    # Linear fit through the means, over the actual contest range
    x_ends = np.array([x.min(), x.max()])
    ax.plot(x_ends, p(x_ends), linestyle='--', linewidth=2,
            color=theme['trend'], zorder=4)

    # Direct-label the two ends of the fit - the one number this chart is about -
    # rather than annotating every point. Labels sit inside the axes, above the
    # line, so neither end is clipped by the figure edge.
    for xi, ha, dx in ((x_ends[0], 'left', 3), (x_ends[1], 'right', -3)):
        ax.annotate(f'{p(xi):,.0f}', xy=(xi, p(xi)), xytext=(dx, 11),
                    textcoords='offset points', ha=ha, va='bottom',
                    fontsize=9.5, fontweight='bold', color=theme['trend'],
                    bbox=dict(boxstyle='round,pad=0.25', facecolor=theme['surface'],
                              edgecolor='none', alpha=0.9), zorder=5)

    # Chrome: keep only the bottom rule, as a hairline
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color(theme['axis'])
    ax.spines['bottom'].set_linewidth(0.8)

    ax.xaxis.set_major_locator(MaxNLocator(nbins=14, integer=True, steps=[1, 2, 5, 10]))
    ax.yaxis.set_major_locator(MultipleLocator(500))
    ax.tick_params(axis='both', which='both', length=0, colors=theme['muted'], labelsize=9)
    ax.margins(x=0.015, y=0.08)

    ax.set_ylabel('Problem rating', fontsize=9.5, color=theme['secondary'], labelpad=8)
    ax.set_xlabel('Contest number', fontsize=9.5, color=theme['secondary'], labelpad=8)

    legend = ax.legend(
        handles=[
            Line2D([0], [0], color=theme['series'], alpha=theme['range_alpha'],
                   linewidth=3, label='Min-max range'),
            Line2D([0], [0], color='none', marker='o', markersize=6,
                   markerfacecolor=theme['series'], markeredgecolor=theme['surface'],
                   label='Mean rating'),
            Line2D([0], [0], color=theme['trend'], linewidth=2, linestyle='--',
                   label=f'Linear trend ({slope * 100:+.0f} per 100 contests)'),
        ],
        loc='lower left', bbox_to_anchor=(0, 1.01), ncol=3, frameon=False,
        fontsize=9.5, handlelength=1.8, columnspacing=1.8, borderpad=0,
        labelcolor=theme['secondary'],
    )
    for text in legend.get_texts():
        text.set_color(theme['secondary'])


def plot_contest_ratings(candlestick_df, output_stem, title, subtitle):
    # One fit for both renders, so the light and dark PNGs report the same numbers
    z = np.polyfit(candlestick_df['Contest'], candlestick_df['Mean'], 1)
    trend = (np.poly1d(z), z[0])

    for mode, theme in THEMES.items():
        fig, ax = plt.subplots(figsize=(14, 6.5), facecolor=theme['surface'])
        ax.set_facecolor(theme['surface'])
        fig.subplots_adjust(left=0.055, right=0.985, top=0.80, bottom=0.13)

        _draw(ax, candlestick_df, theme, trend)

        fig.text(0.055, 0.965, title, ha='left', va='top',
                 fontsize=16, fontweight='bold', color=theme['ink'])
        fig.text(0.055, 0.905, subtitle, ha='left', va='top',
                 fontsize=10.5, color=theme['secondary'])
        fig.text(0.985, 0.025, SOURCE_NOTE, ha='right', va='bottom',
                 fontsize=8, color=theme['muted'])

        suffix = '' if mode == 'light' else '_dark'
        fig.savefig(f'{output_stem}{suffix}.png', facecolor=theme['surface'])
        plt.close(fig)


def main():
    # Load the data from the file
    file_path = 'leetcode_problem_rating/ratings.txt'
    data = pd.read_csv(file_path, sep='\t')

    # Separate weekly and biweekly contests. Anchor the weekly match, otherwise
    # 'weekly-contest' also matches 'biweekly-contest' and the two series land on
    # top of each other at the same contest numbers.
    weekly_data = data[data['Contest Slug'].str.match(r'weekly-contest-')]
    biweekly_data = data[data['Contest Slug'].str.match(r'biweekly-contest-')]

    charts = [
        (weekly_data, True, 'leetcode_weekly_ratings_top2',
         'LeetCode Weekly Contest Ratings', 'Two hardest problems per contest'),
        (weekly_data, False, 'leetcode_weekly_ratings',
         'LeetCode Weekly Contest Ratings', 'All problems per contest'),
        (biweekly_data, True, 'leetcode_biweekly_ratings_top2',
         'LeetCode Biweekly Contest Ratings', 'Two hardest problems per contest'),
        (biweekly_data, False, 'leetcode_biweekly_ratings',
         'LeetCode Biweekly Contest Ratings', 'All problems per contest'),
    ]

    for source, top_two_only, output_stem, title, scope in charts:
        candlestick_df = get_contest_ratings(source, top_two_only=top_two_only)
        subtitle = (f'{scope} · {len(candlestick_df)} contests '
                    f'({candlestick_df["Contest"].min()}–{candlestick_df["Contest"].max()})')
        plot_contest_ratings(candlestick_df, output_stem, title, subtitle)


if __name__ == "__main__":
    main()
