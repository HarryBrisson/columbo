# columbo
automated police scanner audio collection, analysis and presentation to empower community leaders

created for [The Opioid Hackathon 2018](https://www.theopioidhackathon.com/)

# Why It Matters
For county public health officials, knowing when abnormally high rates of overdoses take place can save lives.  Using audio feeds publicly available on broadcastify.com, **columbo** helps provide near real-time information to those who need it most.

# Getting Started

`git clone https://github.com/HarryBrisson/columbo.git`

`cd columbo`

`bash initialize.sh`

This particular version requires aws credentials to store data in a `columbo-scanner-data` bucket.

`python3`

`from scan import *`

`surf_scanners('los angeles')`
