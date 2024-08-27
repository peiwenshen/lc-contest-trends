import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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

def plot_contest_ratings(candlestick_df, output_filename, title):
    # Plot the Candlestick chart with Mean values
    plt.figure(figsize=(20, 8))  # Make the graph wider

    # Plot the min-max vertical lines for each contest
    plt.vlines(candlestick_df['Contest'], candlestick_df['Min'], candlestick_df['Max'], color='black')

    # Plot the mean value points
    plt.scatter(candlestick_df['Contest'], candlestick_df['Mean'], color='blue', marker='o', s=80)  # Blue mean point with larger size

    # Calculate and plot the trend line for the mean values
    z = np.polyfit(candlestick_df['Contest'], candlestick_df['Mean'], 1)
    p = np.poly1d(z)
    
    # Generate x values spanning the entire range of contests
    x_values = np.linspace(candlestick_df['Contest'].min(), candlestick_df['Contest'].max(), candlestick_df['Contest'].max())
    plt.plot(x_values, p(x_values), "r--", label='Trend Line')

    plt.xticks(candlestick_df['Contest'], rotation=90)
    plt.ylabel('Rating')
    plt.xlabel('Contest')
    plt.title(title)
    plt.legend()

    # Save the plot to the current directory
    plt.savefig(output_filename, bbox_inches='tight')

    # Show the plot
    plt.show()

def main():
    # Load the data from the file
    file_path = 'leetcode_problem_rating/ratings.txt'
    data = pd.read_csv(file_path, sep='\t')

    # Separate weekly and biweekly contests
    weekly_data = data[data['Contest Slug'].str.contains('weekly-contest')]
    biweekly_data = data[data['Contest Slug'].str.contains('biweekly-contest')]

    # Process and plot for weekly contests
    candlestick_df = get_contest_ratings(weekly_data, top_two_only=True)
    plot_contest_ratings(candlestick_df, 'leetcode_weekly_ratings_top2.png', 'LeetCode Weekly Contest Ratings - Top 2')

    candlestick_df = get_contest_ratings(weekly_data, top_two_only=False)
    plot_contest_ratings(candlestick_df, 'leetcode_weekly_ratings.png', 'LeetCode Weekly Contest Ratings - All Ratings')

    # Process and plot for biweekly contests
    candlestick_df = get_contest_ratings(biweekly_data, top_two_only=True)
    plot_contest_ratings(candlestick_df, 'leetcode_biweekly_ratings_top2.png', 'LeetCode Biweekly Contest Ratings - Top 2')

    candlestick_df = get_contest_ratings(biweekly_data, top_two_only=False)
    plot_contest_ratings(candlestick_df, 'leetcode_biweekly_ratings.png', 'LeetCode Biweekly Contest Ratings - All Ratings')

if __name__ == "__main__":
    main()