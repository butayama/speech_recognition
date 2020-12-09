#tl;dr

## setting up a branch to track a repo

_pre_: assuming you have forked a repo and cloned your fork to your computer

1. `git remote add [maintainer's name] [paste URL here]`
1. `git fetch --all`
1. `git branch --track [maintainer's name]_[branch] [remote name from step 1]/[branch you want to track]`
At this point you may watch to checkout to your newly create branch and issue a `git pull` command.

## Fetching updates from the maintainer's repo
1. `git checkout [maintainer's name]_[branch]`
1. `git pull`
1. `git checkout master`
1. `git merge [maintainer's name]_[branch]`

====

# You've Forked Up

These are notes for someone who has forked a Repository(Repo) on Github and would like to update their forked copy with updates from the Original Repo.

For example, Let's imagine that I have cloned jQuery to my Github Account. A few days later through some notifications, jQuery has updated the Repo with new code, after some review I decide that I want this code. People new to Github/Git would delete the fork that is on their own account, then just Fork the Repo again. While this would work, it is extremely uncool (we want to be cool, right?).

The steps below outline how to set up a branch, add a new `remote` which points to the Original Repo, and then set up the branch to track the Original Repo, for easier and quicker updates. These steps are performed in your command-line interface and once set-up for a project, it takes at least 4 commands to update and merge in changes.

From here on out I will refer to the Original Repo as `Maintainer's ...`.

# Be Clean (step 1)
`git status` to ensure that you are working _clean_ and can run the commands below. If your repo is not _clean_ please do all the steps needed to get clean (e.g. commit, stash).

# Add Original Repo's HTTPS URL (step 2)
Go to the Original Repo's Github page and get the `https` Clone URL. It should look something like `https://github.com/jquery/jquery.git`

With the URL copied to your clipboard. Run the command below in your Terminal. Here at DevLeague we prefer giving our tracking remote a name that includes the Original Repo's name followed by a `_origin` suffix.

#### Here is an example using the jQuery repo

    git remote add jquery_origin https://github.com/jquery/jquery.git

#### command break down

    git remote add [maintainer's name] [paste URL here]

## After you have added a new remote
Make sure to run the fetch command, fetch goes and updates the history of a certain remote ([and so much more](http://git-scm.com/docs/git-fetch))

#### using the example with jquery from above

    git fetch jquery_origin

# Add Tracking Branch (step 3)
_before_: run the command `git fetch --all`
Our convention is to name the branch with the [maintainer's name] and a `_[branch]` suffix.

    git branch --track jquery_master jquery_origin/master

#### command break down

    git branch --track [maintainer's name]_[branch] [remote name from step 2]/[branch you want to track]
    
#### Before moving on...

    git checkout [maintainer's name]_[branch]

# Update Upstream's Master (Step 4)
Now that you've added a remote, created a new branch, and set that it (your newly created branch) to track a branch on the Original Repo. Now you can pull down changes!

#### run the command

    git pull

You should see some changes mentioned in the Terminal.

# Merge Upstream's commits (Step 5)

Now checkout to your own local working branch and merge in the changes from your branch original repo tracking branch.

# Last Words
Once you have done all these steps for one repo, to get updates in the future all you need to do is *Steps 4 & 5*. If you have a new project, you *MUST* do all the steps over again to set up a tracking branch, new origin, etc.