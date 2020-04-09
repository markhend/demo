import collections, conducto as co, json, re

# Data is downloaded from the United States Energy Information Administration.
# https://www.eia.gov/opendata/bulkfiles.php

PERM_DATA_PATH = "conducto/demo/data_science/steo.txt"

DOWNLOAD_COMMAND = f"""
echo "Downloading"
curl http://api.eia.gov/bulk/STEO.zip > steo.zip
unzip -cq steo.zip | conducto-perm-data puts --name {PERM_DATA_PATH}
""".strip()

DATASETS = {
    "Heating Degree Days"   : r"^STEO.ZWHD_[^_]*\.M$",
    "Cooling Degree Days"   : r"^STEO.ZWCD_[^_]*.M$",
    "Electricity Generation": r"^STEO.NGEPGEN_[^_]*\.M$"
}

IMG = co.Image("python:3.8", copy_dir=".", reqs_py=["conducto", "pandas", "matplotlib", "tabulate"])


def run() -> co.Serial:
    """
    Pipeline that downloads data from the US EIA and visualizes it.
    """
    with co.Serial(image=IMG) as output:
        # First download some data from the US Energy Information Administration.
        output["Download"] = co.Exec(DOWNLOAD_COMMAND)

        # Then make a few different visualizations of it.
        output["Display"] = co.Parallel()
        for dataset in DATASETS.keys():
            output["Display"][dataset] = co.Exec(f"python intro.py display --dataset='{dataset}'")
    return output


def display(dataset):
    """
    Read in the downloaded data, extract the specified datasets, and plot them.
    """
    data_text = co.perm_data.gets(PERM_DATA_PATH)
    all_data = [json.loads(line) for line in data_text.splitlines()]

    regex = DATASETS[dataset]
    subset_data = [d for d in all_data if "series_id" in d and re.search(regex, d["series_id"])]

    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    import pandas as pd
    import numpy as np

    # Create a pandas DataFrame with the data grouped by month of the year. This could
    # be implemented with vectorized pandas logic but this data is small enough not to
    # worry.
    data = {}
    for i, d in enumerate(subset_data):
        by_month = collections.defaultdict(list)
        for yyyymm, value in d["data"]:
            month = int(yyyymm[-2:])
            by_month[month].append(value)
        y = [np.mean(by_month[month]) for month in range(1, 13)]
        data[d['name']] = y

    df = pd.DataFrame(data=data)
    df["Month"] = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    df.set_index("Month", inplace=True)

    # Graph each dataset as one line on a single plot.
    colors = [cm.viridis(z) for z in np.linspace(0, .99, len(subset_data))]
    for i, column in enumerate(df.columns):
        y = df[column].values
        plt.plot(y, label=column, color=colors[i])
    plt.title(f"{dataset}, average by month")
    plt.legend(loc="best", fontsize="x-small")

    # Save to disk, and then to co.temp_data
    filename = "/tmp/image.png"
    dataname = f"conducto/demo/data_science/{dataset}.png"
    plt.savefig(filename)
    co.temp_data.put(dataname, filename)

    # Print out results as markdown
    print(f"""
<ConductoMarkdown>
![img]({co.temp_data.url(dataname)})

{df.transpose().round(2).to_markdown()}
</ConductoMarkdown>
    """)


if __name__ == "__main__":
    co.main()