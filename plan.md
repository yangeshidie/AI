
    {
      "role": "assistant",
      "content": "![Generated Image](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAABYAAAAMACAIAAAASU1SbAAAAiXpUWHRSYXcgcHJvZmlsZSB0eXBlIGlwdGMAAAiZTYwxDgIxDAT7vOKekDjrtV1T0VHwgbtcIiEhgfh/QaDgmGlWW0w6X66n5fl6jNu9p+ULkapDENgzpj+Kl5aFfa6KnYWgSjZjGOiSYRxTY/v8KIijI/rXyc236kHdAK22RvHVummEN+………………91ML0BQ+siou79WmMAAAKHaVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49Iu+QmTxcHmLKBUdi6n2VsOvwC0NTwN4S7ADAzLGvcQIHMlHKHDRBJPYSghMhijpTitwDQnBCNc0c0QDBn4GZhWdEDDganWCxW3j4QAZZyjQMKeOpogKBafzWu6OnXhNyTXt0iagEmYcUXAaE5Ns6i9JXj1jCetuYO3QNqYsJQHROOCCZDeFDPxPZmNdxD101THPYnYFYTayqq4BhSgkZDQz6mdZXkVabOWAiQoou6taEmcBNzOq2IpEJmJsmd7eUWLSZajVj4t08mwlzNvOmcrlc1A2jMO9TJFQu63Kp20nXu7uXOSV3ZwRknsvucNiVRIdpMtddNjXR1ZqGbuvt82sjz7Mvbf2p3//bh/tdHx499UXtc5C7KPlXCS15lK4QzBJIQQSdBpoZsn7wgBgQIsIcPRcZeVS5i4fxOvaCSntrpZKQvq4LV+tHkSIgXl3yQc4AsLifp1EcHd8RUtgYGar7zZqAIcw64zi7v8XcMnK3JC1N2UAAAAASUVORK5CYII=)"
    }
    有时候还会：
    {
    "role": "assistant",
    "content": "**Reasoning:**\n**Analyzing Consistency of Style**\n\nI am now focused on ensuring the second page of the manga mirrors the first. The plan involves replicating the clean lines, halftone shading, and watercolor coloring. Additionally, I'm working to maintain character consistency.\n\n\n**Implementing Manga Page Two**\n\nI'm currently focused on the details for the second manga page. I've broken it down to style, character consistency, page layout, and content. The page will utilize a four-panel structure with a left-to-right reading order. The content will depict the two characters discussing homework in various shots and I plan on adding clear dialogue boxes with Chinese text.\n\n\n**Verifying Page Compliance**\n\nI'm checking the generated comic page against the initial prompts. The art style from the first page is consistently applied, and character consistency is good. New character interactions feel natural. The composition, perspective, and emotional expression within the four-panel layout align with the input. The text and its placement are accurate.\n\n\n**Confirming Visual Elements**\n\nI'm confirming the page's adherence to the original description. The comic page maintains the previous Japanese school manga style. The main characters look consistent, and the new character interactions are seamless. The four-panel layout's composition, perspectives, and emotional content directly reflect the prompt. Text and its arrangement also match the instructions.\n\n\n\n\n**Response:**\n![Generated Image](data:image/png;base64,
    ……………… +5lNyUGJyzcTBlkz2FC6pHZXYjNQGT9w3zDGjF296DUZTC7Jk9EvTX6IjUxU82HSmRs5JDuDuw2dvPWkeMBYErSByhdAWcG5dmozauFF3inQZOCHgxZ/D/zedM4gU3RMKkOKFqk9yFdOR2aNzmrWsCbC2TRzfKh4K2X0BJ0CWGpDlGo1JrhFFA6DWsD5gJn2n8py2Mvsqn/LYjvWDtsrKfZKgs6BWXrsk2qzpE84R/KHaRdtQzZzwl2IL8rJoKFpHbLG3roLZ7sL2LdSzMIf2cGoLzdSR2pc5AuGjNEV6pSPtI3oBuLu1aWhMz6Wjve4j93fTwEIR8cLTAKiTXRAX9xSJ2I6WfCbgF0+Cv0pUlbrjC0Y3ujRAR/xsVbQW4SWp8ZzEjkFxwKLqFggekiBdSJUb8vz4+aTP1QIs4jqT+g+go684pfeCUEfD8Tl5YBKbqSElqTpwSv/7hPOG7MxiwfcCqmsSgPYrbojDbDe66Q6/3Hr3ZjbmbK27X5vZmCqJesL/u05mHegUYm9r79eKtAH8rLc+s/5N6By/BPVPYkWrK6PjgDoV9zF4clCD7IKYz0p3kkhB3jMFEc3Z4v59o4N9rj27ud+RXoXNqeFmLY5/hGbajIpAUMJEM5/sEt7cHSxiaHD3/w9fn2vdZ8lfVAAAAABJRU5ErkJggg==)"
    }
 上面是经典的从LLM出获取的图片的格式，但是我不可能在这个的基础上去跟它继续聊天，因为这些东西都在content里面，会记录到token里面，所以需要修改history和chat里面的逻辑，检测到
 图片的生成就把图片保存到某个区域
 就比如说这样的{
        "type": "image_url",
        "image_url": {
          "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAABYAAAAMA………………………………9ZuqcRwPFJThRGfKTyDvI1aRbpcA7NAeNXqNz9vBgAJvKqw8wUA3RmUWJrU72jr4hBoYhkkt7lpn0L4++Ff2Snm3QSeUVLp+P3qeWc7CLAjaeV3jYuVS7+QbVDB2miCa+5wkPp49HY7E8h6PcfEYoI4YH/5qeE6LncCmvZ3s/+dXbIOIi6ja7UW6OGYI3lYLLR39uVxLrqC2e1jfal9i95Abca/ESHCm0Vo50X6Cmd04t4rjMlp4xKkFiI7gzi8s3B8HfH2TBypbGLyHgyr/gHmjYoofprlpQAAAABJRU5ErkJggg=="
        }
      }
 整体就是这样
 [
  {
    "role": "user",
    "content": [
      {
        "type": "text",
        "text": "生成第 2 页漫画，使用之前生成的主角参考图：\n\n全局要求：\n- 漫画风格：日式校园全彩漫画，干净线条，轻微网点阴影\n- 所有格子保持角色外观一致\n- 对白框文字清晰，不溢出\n- 分辨率高，适合高清阅读\n- 气氛：轻松、日常校园互动\n\n页面结构：\n- 分镜数量：4 格\n- 阅读方向：从左到右\n\n分镜描述：\n\n第 1 格：\n- 镜头：中景\n- 角度：平视\n- 画面：主角身边坐下一个同学，手里拿着作业本\n- 表情：微笑，友善\n- 对白（同学说）：「嘿，你看过老师布置的作业吗？」\n\n第 2 格：\n- 镜头：近景\n- 角度：平视\n- 画面：主角看向作业本，手指轻点书页\n- 表情：微笑、略带疑惑\n- 对白（主角说）：「还没呢，让我看看……」\n\n第 3 格：\n- 镜头：中景\n- 角度：俯视\n- 画面：桌面上两本作业本对开，主角和同学交流讨论\n- 表情：专注、轻松\n- 对白（主角内心独白）：「原来这道题有点意思……」\n\n第 4 格：\n- 镜头：特写\n- 角度：正面\n- 画面：主角嘴角微微上扬，眼睛闪光\n- 表情：略带得意\n- 对白（内心独白）：「看来今天也不会无聊呢！」\n\n补充说明：\n- 保持与第 1 页完全一致的画风、线条、角色比例与视觉风格\n- 背景适度留白，突出主角与互动的同学\n- 对白框字体清晰可读"
      },
      {
        "type": "image_url",
        "image_url": {
          "url": "data:image/png;base64,
 ……………………