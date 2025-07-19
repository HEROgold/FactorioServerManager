type Redirectable = {
    redirect: (url: string) => void;
}

export default function discord(res: Redirectable) {
    res.redirect('https://discord.gg/qPe4wtHuJR');
}
