// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title VantaNFT
 * @dev ERC721 with Lazy Minting (gasless listing) and Dynamic Commission
 */
contract VantaNFT is ERC721, ReentrancyGuard, Ownable {
    uint256 private _nextTokenId;
    uint256 public constant COMMISSION_SHORT = 200;   // 2% (basis points)
    uint256 public constant COMMISSION_LONG = 1500;  // 15% (basis points)
    uint256 public constant BASIS_POINTS = 10000;
    uint256 public constant THIRTY_DAYS = 30 days;

    struct Listing {
        uint256 tokenId;
        address seller;
        uint256 price;
        uint256 listingTime;
        bool active;
    }

    mapping(uint256 => Listing) public listings;
    mapping(uint256 => string) private _tokenURIs;

    event Listed(uint256 indexed tokenId, address indexed seller, uint256 price, uint256 listingTime);
    event Sold(uint256 indexed tokenId, address indexed buyer, address indexed seller, uint256 price, uint256 commission);
    event Delisted(uint256 indexed tokenId);

    constructor() ERC721("VantaNFT", "VNTA") Ownable(msg.sender) {}

    /**
     * @dev Lazy listing - no minting until purchase
     */
    function listForSale(uint256 price, string calldata tokenURI) external returns (uint256) {
        require(price > 0, "Price must be > 0");
        uint256 tokenId = _nextTokenId++;
        _tokenURIs[tokenId] = tokenURI;

        listings[tokenId] = Listing({
            tokenId: tokenId,
            seller: msg.sender,
            price: price,
            listingTime: block.timestamp,
            active: true
        });

        emit Listed(tokenId, msg.sender, price, block.timestamp);
        return tokenId;
    }

    /**
     * @dev Buy token - mints on purchase with dynamic commission
     */
    function buyToken(uint256 tokenId) external payable nonReentrant {
        Listing storage listing = listings[tokenId];
        require(listing.active, "Not for sale");
        require(msg.value >= listing.price, "Insufficient payment");
        require(msg.sender != listing.seller, "Cannot buy own listing");

        uint256 duration = block.timestamp - listing.listingTime;
        uint256 commissionBps = duration < THIRTY_DAYS ? COMMISSION_SHORT : COMMISSION_LONG;
        uint256 commission = (listing.price * commissionBps) / BASIS_POINTS;
        uint256 sellerAmount = listing.price - commission;

        listing.active = false;

        // Mint to buyer
        _safeMint(msg.sender, tokenId);

        // Transfer ETH
        (bool sentSeller,) = payable(listing.seller).call{value: sellerAmount}("");
        require(sentSeller, "Transfer to seller failed");

        if (commission > 0) {
            (bool sentOwner,) = payable(owner()).call{value: commission}("");
            require(sentOwner, "Commission transfer failed");
        }

        // Refund excess
        if (msg.value > listing.price) {
            (bool sentRefund,) = payable(msg.sender).call{value: msg.value - listing.price}("");
            require(sentRefund, "Refund failed");
        }

        emit Sold(tokenId, msg.sender, listing.seller, listing.price, commission);
    }

    function delist(uint256 tokenId) external {
        Listing storage listing = listings[tokenId];
        require(listing.active, "Not active");
        require(listing.seller == msg.sender, "Not seller");
        listing.active = false;
        emit Delisted(tokenId);
    }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        require(_ownerOf(tokenId) != address(0) || listings[tokenId].active, "Nonexistent token");
        return _tokenURIs[tokenId];
    }

    function getListing(uint256 tokenId) external view returns (
        address seller,
        uint256 price,
        uint256 listingTime,
        bool active,
        uint256 commissionBps
    ) {
        Listing storage l = listings[tokenId];
        uint256 duration = block.timestamp - l.listingTime;
        uint256 bps = duration < THIRTY_DAYS ? COMMISSION_SHORT : COMMISSION_LONG;
        return (l.seller, l.price, l.listingTime, l.active, bps);
    }
}
